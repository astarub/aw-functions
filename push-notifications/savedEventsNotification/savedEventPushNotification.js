const appwrite = require('node-appwrite');
const admin = require('firebase-admin');
const axios = require('axios');

// Firebase service account
const serviceAccount = require("./service-account.json");

// Initialize firebase 
admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

// Function to split array into chunks
function chunk(array, chunkSize) {
    var arr = [];
    for (let i = 0; i < array.length; i += chunkSize) {
        const chunk = array.slice(i, i + chunkSize);
        arr.push(chunk);
    }
    return arr;
}

module.exports = async (req, res) => {
    // Set appwrite endpoint
    const client = new appwrite.Client()
        .setEndpoint('https://api-app2.asta-bochum.de/v1')
        .setProject('campus_app')                
        .setKey(req.variables.API_KEY);

    const db = new appwrite.Databases(client);

    // Get all events from the asta calendar 
    let wpEvents;
    try {
        wpEvents = (await axios('https://asta-bochum.de/wp-json/tribe/events/v1/events')).data.events;
        
    } catch(e) {
        console.log('[ERROR] Could not fetch AStA Events.');
        return res.json("Error");
    }

    // Get all events from the app calendar 
    try {
        wpEvents = wpEvents.concat((await axios('https://app2.asta-bochum.de/wp-json/tribe/events/v1/events')).data.events);
        
    } catch(e) {
        console.log('[ERROR] Could not fetch App Events.');
        return res.json("Error");
    }

    // Get all events without duplicates 
    const events = (await db.listDocuments('push_notifications', 'saved_events')).documents;
    const uniqueEvents = [...new Map(events.map(item => [item['eventId'], item])).values()];

    const today = new Date(Date.now());
    
    // Get all events that happen today 
    const eventsToday = uniqueEvents.filter((item) => {
        const date = new Date(Date.parse(item.startDate));

        return date.getFullYear() == today.getFullYear() && date.getMonth() == today.getMonth() && date.getDate() == today.getDate();
    });

    // Go through all events 
    for (const eventToday of eventsToday) {
        // Find the corresponding event of the AStA calendar 
        const wpEvent = wpEvents.find(event => event.id == eventToday.eventId);
        if(wpEvent == undefined) continue;
    
        // Adjust the notification body based on the existence of an end date
        const time = (wpEvent.start_date_details.hour == wpEvent.end_date_details.hour && 
            wpEvent.start_date_details.minutes == wpEvent.end_date_details.minutes) ? 
                `Heute ${wpEvent.start_date_details.hour}:${wpEvent.start_date_details.minutes} Uhr` 
            : `Heute ${wpEvent.start_date_details.hour}:${wpEvent.start_date_details.minutes} bis ${wpEvent.end_date_details.hour}:${wpEvent.end_date_details.minutes} Uhr`
        ;
        
        // Send the message
        await admin.messaging().send(
            {
                notification: {
                    title: `Erinnerung ${wpEvent.title}!`,
                    body: `${time} ${wpEvent.venue.venue != undefined ? `Ort: ${wpEvent.venue.venue}` : ''}`,
                },  
                android: {
                    notification: {
                        priority: "high",
                        channelId: 'savedEvents'
                    }
                },
                apns: {
                    headers: {
                        'apns-priority': '10'
                    },
                    payload: {
                        aps: {
                            contentAvailable: true,
                            category: 'savedEvents'
                        }
                    }
                },
                data: {
                    "interaction": String(JSON.stringify({
                        "destination": 'calendar',
                        "data": [
                            {
                                "event": {
                                    "id": eventToday.eventId
                                }
                            }
                        ]
                    }))
                },
                topic: eventToday.eventId.toString()
            }
        );
    
        console.log('[INFO] Notifications sent.');
    
        // Remove all documents with the corresponding event id 
        const eventDocuments = events.filter(item => item.eventId == eventToday.eventId);
        for (const eventDocument of eventDocuments) {
            try {
                await db.deleteDocument('push_notifications', 'saved_events', eventDocument.$id);
            } catch (e)  {
                console.log('[ERROR] Error while deleting saved events:' + e);
                continue;
            }
        }
    
        console.log('[INFO] Documents deleted.');
    
        // Get all fcm tokens of the documents with the corresponding event id 
        const fcmTokens = eventDocuments.map(item => item.fcmToken);
        const tokenChunks = chunk(fcmTokens, 1000);
    
        // Unsubscribe all devices from the topic to delete it
        for (const chunk of tokenChunks) {
            try {
                await admin.messaging().unsubscribeFromTopic(chunk, eventToday.eventId.toString());
            } catch (e) {
                console.log('[ERROR] Error while unsubscribing tokens: ' + e);
            }
        }
    
        console.log('[INFO] Topic deleted.');
    }
    console.log('[INFO] All operations concluded. Closing...')
    return res.json("Function executed!");
};