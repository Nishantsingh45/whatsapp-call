# Setup Guide for the OpenAI Realtime SIP Voice Bot

This guide will walk you through the process of setting up and running the OpenAI Realtime SIP Voice Bot. This project uses Twilio for SIP trunking and OpenAI's Realtime API to power the voice bot.

## 1. Prerequisites

Before you begin, you will need the following:

*   A [Twilio account](https://www.twilio.com/try-twilio)
*   An [OpenAI account](https://platform.openai.com/) with access to the Realtime API.
*   [Node.js](https://nodejs.org/) (version 22.15.0 or higher)
*   [ngrok](https://ngrok.com/download) for tunneling your local server to the internet.

## 2. OpenAI Setup

### 2.1. Get your API Key and Project ID

1.  Log in to your [OpenAI account](https://platform.openai.com/).
2.  Navigate to the [API keys](https://platform.openai.com/api-keys) page and create a new secret key. Copy this key and save it for later.
3.  Go to your [Project settings](https://platform.openai.com/settings) to find your **Project ID**. You will need this for the Twilio setup.

### 2.2. Create a Webhook

1.  In your OpenAI project settings, go to the [Webhooks](https://platform.openai.com/webhooks) page.
2.  Click on the "Create a webhook" button.
3.  Give your webhook a name (e.g., "Realtime SIP Bot").
4.  For the "URL", you will need to use an `ngrok` URL. We will set this up in the "Local Setup" section. For now, you can use a placeholder like `https://your-ngrok-domain.ngrok.io`.
5.  For the "Event type", select `realtime.call.incoming`.
6.  Click "Create".
7.  After the webhook is created, copy the **Webhook secret**. You will need this for your `.env` file.

## 3. Twilio Setup

### 3.1. Buy a Phone Number

1.  Log in to your [Twilio account](https://console.twilio.com/).
2.  Go to the [Buy a Number](https://console.twilio.com/us1/develop/phone-numbers/search) page.
3.  Search for a number with **Voice** capabilities and purchase it.

### 3.2. Create a SIP Trunk

1.  Go to the [SIP Trunks](https://console.twilio.com/us1/develop/voice/sip-trunks) page in the Twilio console.
2.  Click on the "+" button to create a new SIP trunk.
3.  Give it a name (e.g., "OpenAI SIP Trunk").

### 3.3. Configure the SIP Trunk

1.  In your newly created SIP trunk, go to the **Origination** tab.
2.  Click on "Add Origination URI".
3.  Set the URI to `sip:YOUR_OPENAI_PROJECT_ID@sip.api.openai.com;transport=tls`, replacing `YOUR_OPENAI_PROJECT_ID` with the Project ID you got from the OpenAI console.
4.  Leave the priority and weight as default.
5.  Go to the **Phone Numbers** tab.
6.  Click on "Add Phone Number" and select the number you purchased earlier.

## 4. Local Setup

### 4.1. Install Dependencies

Clone this repository to your local machine and navigate to the project directory. Then, run the following command to install the necessary dependencies:

```bash
npm install
```

### 4.2. Set up Environment Variables

1.  This project uses a `.env` file to store your credentials. You will see a file named `.env` in the root of the project.
2.  Open the `.env` file and replace the placeholder values with your actual credentials:

```
OPENAI_API_KEY="your_openai_api_key"
OPENAI_WEBHOOK_SECRET="your_openai_webhook_secret"
PORT=8000
```

### 4.3. Run the Server

Start the server by running the following command:

```bash
npm run dev
```

The server will start on port 8000.

## 5. Testing

### 5.1. Start ngrok

Open a new terminal window and run the following command to expose your local server to the internet:

```bash
ngrok http 8000
```

`ngrok` will give you a public URL (e.g., `https://abcdef123456.ngrok.io`).

### 5.2. Update the Webhook URL

1.  Go back to your [OpenAI Webhooks page](https://platform.openai.com/webhooks).
2.  Edit the webhook you created earlier.
3.  Replace the placeholder URL with the `ngrok` URL you just got. Make sure to append the correct path if your server has one (in this case, the root path `/` is used).

### 5.3. Place a Call

You are now ready to test the voice bot. Call the Twilio phone number you purchased. You should be greeted by the OpenAI voice bot. You can then have a conversation with it.

Check the console where you are running the server to see the logs and debug any issues.

That's it! You have successfully set up and run the OpenAI Realtime SIP Voice Bot.
