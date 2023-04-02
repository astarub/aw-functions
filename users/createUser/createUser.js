const appwrite = require('node-appwrite');

module.exports = async (req, res) => {
    let payload;

    try {
        payload = JSON.parse(req.payload);
    } catch(e) {
        return res.json("Invalid JSON payload.", 500);
    }

    if(!payload.api_key || !payload.userId || !payload.email || !payload.password) {
        return res.json("Incorrect request. Please provide an api key, a user id, an email and a password.");
    }

    if(payload.api_key != req.variables.AUTH_KEY) {
        return res.json("Incorrect api key. Please provide a valid api key.");
    }

    // Set appwrite endpoint
    const client = new appwrite.Client()
        .setEndpoint('https://api-app.asta-bochum.de/v1')
        .setProject('campus_app')                
        .setKey(req.variables.API_KEY);

    const users = new appwrite.Users(client);

    try {
        const user = await users.create(payload.userId, payload.email, undefined, payload.password);

        return res.json({id: user.$id});
    } catch (e) {
        console.log(e);
        return res.json("Could not create user. Please try again later.", 500);
    }
}