const admin = require('firebase-admin');

// Firebase service account
const serviceAccount = require("./service-account.json");

// Initialize firebase 
admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

module.exports = async (req, res) => {
    const payload = JSON.parse(req.payload);

    if(!payload.title || !payload.body) {
        return res.json("Incorrect request. Please provide a notification title and body.")
    }

    if(payload.data) {
        await admin.messaging().send(
            {
                notification: {
                    title: payload.title,
                    body: payload.body,
                },  
                android: {
                    notification: {
                        priority: "high",
                        channelId: payload.channel != undefined ? payload.channel : "notifications"
                    }
                },
                apns: {
                    headers: {
                        'apns-priority': '10'
                    },
                    payload: {
                        aps: {
                            contentAvailable: true,
                            category: payload.channel != undefined ? payload.channel : "notifications"
                        }
                    }
                },
                data: {
                    "interaction": String(JSON.stringify(payload.data))
                },
                topic: payload.topic != undefined ? payload.topic : 'defaultNotifications'
            }
        ).catch(error => {
            return res.json(`Error while sending push notification. Error: ${error}`, 400);
        });
    } else {
        await admin.messaging().send(
            {
                notification: {
                    title: payload.title,
                    body: payload.body,
                },  
                android: {
                    notification: {
                        channelId: payload.channel != undefined ? payload.channel : "notifications"
                    }
                },
                apns: {
                    payload: {
                        aps: {
                            category: payload.channel != undefined ? payload.channel : "notifications"
                        }
                    }
                },
                topic: payload.topic != undefined ? payload.topic : 'defaultNotifications'
            }
        ).catch(error => {
            return res.json(`Error while sending push notification. Error: ${error}`, 400);
        });
    }

    return res.json("Push notification sent!");
};