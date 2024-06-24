const appwrite = require('node-appwrite');

module.exports = async ({req, res, log, error}) => {
    // Set appwrite endpoint
    const client = new appwrite.Client()
        .setEndpoint('https://api-app.asta-bochum.de/v1')
        .setProject('campus_app')                
        .setKey(process.env.API_KEY);

    const users = new appwrite.Users(client);
    const db = new appwrite.Databases(client);

    const last_login_accounts = (await db.listDocuments('accounts', 'last_login')).documents;

    const stale_accounts = [];

    for(const account of last_login_accounts) {
        const date = Date.parse(account['date']);
        const past = new Date();
        past.setMonth(past.getMonth() - 4);

        if(date < past) {
            stale_accounts.push(account);
        }
    }

    let deleted = 0;
    for(const account of stale_accounts) {
        try {
            await users.delete(account['userId']);
            deleted++;
        } catch(e) {
            log(e);
            return res.json("Error while deleting an account" + e, 500);
        }
    }

    return res.json(`Deleted ${deleted} accounts.`, 200);
}