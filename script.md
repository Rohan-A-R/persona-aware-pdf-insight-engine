
# Screen Recording Script: HubSpot Integration Walkthrough

**(Start Recording)**

---

### Introduction

"Hi, my name is [Your Name], and today I'll be walking you through the HubSpot integration I built for this technical assessment.

The goal of this feature is to allow a user to securely connect their HubSpot account to our application, and then import their contact data.

The application is built with a React frontend and a Python FastAPI backend."

---

### Part 1: Final Product Functionality

**(Navigate to the application's main page in your browser)**

"Here we have the main interface of our application. As you can see, we have several integration options. We're going to focus on HubSpot.

From a user's perspective, the process is very straightforward.

First, the user clicks on **'Connect to HubSpot'**."

**(Click the 'Connect to HubSpot' button. A popup window should appear)**

"This action opens a secure popup window managed by HubSpot. This is where the user will enter the credentials for their **normal, everyday HubSpot account** - not a developer account. This ensures their credentials are safe and never exposed to our application directly."

**(In the popup, log in using the credentials for your non-developer, "normal" HubSpot test account)**

"After logging in, HubSpot presents the user with an authorization screen. This screen informs the user that our application wants to access their data and clearly lists the permissions, or 'scopes', we are requesting. In this case, that's permission to read contacts and deals. The user clicks **'Choose Account'** and then **'Connect app'** to grant permission."

**(Click the "Choose Account" and "Connect app" buttons in the popup. The popup should close automatically)**

"Once authorization is complete, the popup closes, and the user is returned to our application.

You can see the UI has updated. The button now says **'HubSpot Connected'** and is green, giving the user clear feedback that the connection was successful.

Simultaneously, the application has used this new connection to automatically fetch the user's contacts from the HubSpot API. The data you see displayed here - contact name, creation date, and last modified date - has been loaded directly from the user's account."

**(Briefly scroll or point to the list of loaded contacts)**

"This completes the user-facing functionality. It's a seamless, secure, and user-friendly process for connecting an external account and importing data."

---

### Part 2: Code Discussion

"Now, let's take a brief look at the code that powers this functionality. I'll start with the frontend and then move to the backend."

**(Open your code editor to `frontend/src/integrations/hubspot.js`)**

"The frontend component is built in React. The `handleConnectClick` function is triggered when the user first clicks the connect button. It makes a call to our backend to get the unique HubSpot authorization URL and then opens that URL in the popup window.

When that popup window closes, the `handleWindowClosed` function is called. This function makes another call to our backend to fetch the secure credentials, confirming the connection and triggering the data load."

**(Switch to `backend/main.py` in your code editor)**

"The backend is a FastAPI application. It exposes three key endpoints for the HubSpot integration:
*   `/authorize`: To generate the initial authorization URL.
*   `/oauth2callback`: This is the secure redirect URI that HubSpot calls back to after the user logs in.
*   `/load`: This endpoint is used to fetch the data from HubSpot after the connection is established."

**(Switch to `backend/integrations/hubspot.py` in your code editor)**

"This file contains the core logic.

The `authorize_hubspot` function builds the authorization URL. It includes our app's unique Client ID and the specific scopes we're requesting. It also generates a unique 'state' token which is stored in Redis to prevent cross-site request forgery attacks.

The most important function is `oauth2callback_hubspot`. This function handles the secure callback from HubSpot. It verifies the 'state' token, and then exchanges the temporary authorization code that HubSpot provides for a permanent access token. This token is then encrypted and stored securely in our Redis database, associated with the user's account.

Finally, the `get_items_hubspot` function is called. It retrieves the user's stored access token from Redis and uses it to make an authenticated request to the HubSpot API to fetch the user's contacts. This data is then formatted and sent back to the frontend to be displayed."

---

### Conclusion

"So, to summarize, we have a seamless and secure user experience on the frontend, which is powered by a robust backend that handles the entire OAuth 2.0 flow, from generating the authorization request to securely storing credentials and fetching data.

This demonstrates a complete, end-to-end integration with the HubSpot API.

Thank you for watching."

**(End Recording)**
