# Privacy Agent Backend

This is the backend service for the Privacy Agent application, which provides a secure and privacy-focused way to manage user data and interactions.

## Prerequisites

- Python 3.8 or higher
- Firebase project with Firestore database
- Clerk account for authentication

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd privicyagentbackend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   FIREBASE_PROJECT_ID=your-firebase-project-id
   FIREBASE_PRIVATE_KEY_ID=your-firebase-private-key-id
   FIREBASE_PRIVATE_KEY=your-firebase-private-key
   FIREBASE_CLIENT_EMAIL=your-firebase-client-email
   FIREBASE_CLIENT_ID=your-firebase-client-id
   FIREBASE_CLIENT_X509_CERT_URL=your-firebase-client-x509-cert-url
   CLERK_SECRET_KEY=your-clerk-secret-key
   ```

   Note: For the `FIREBASE_PRIVATE_KEY`, you need to replace the newlines with `\n` characters.

4. Run the application:
   ```
   uvicorn main:app --reload
   ```

## API Endpoints

- `POST /api/chat`: Send a message to the chat
- `GET /api/chat/history`: Get the chat history for the current user
- `POST /api/chat/clear`: Clear the chat history for the current user

## Authentication

The application uses Clerk for authentication. All API endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Database

The application uses Firebase Firestore to store chat messages and user data. The database structure is as follows:

- `users`: Collection of user documents
  - `{userId}`: Document containing user data
    - `email`: User's email address
    - `name`: User's name
    - `createdAt`: Timestamp when the user was created
- `chats`: Collection of chat documents
  - `{chatId}`: Document containing chat data
    - `userId`: ID of the user who owns the chat
    - `messages`: Array of message objects
      - `role`: Role of the message sender (user or assistant)
      - `content`: Content of the message
      - `timestamp`: Timestamp when the message was sent

## License

This project is licensed under the MIT License - see the LICENSE file for details.