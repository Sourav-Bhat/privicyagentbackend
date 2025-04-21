# Policy Pal API Documentation

## Overview

This document provides detailed specifications for the Policy Pal API, which powers the Policy Pal Browser Extension. The API allows users to analyze privacy policies, manage preferences, track analysis history, and access extension-specific features.

## Base URL

```
http://localhost:3000
```

## Authentication

All API endpoints require authentication using a JWT token. Include the token in the Authorization header:

```
Authorization: Bearer <token>
```

## API Endpoints

### Policy Analysis

#### Analyze Policy

Analyzes a privacy policy for a given URL.

```
GET /api/policies/{url}
```

**URL Parameters:**
- `url` (string, required): The URL of the website whose privacy policy should be analyzed

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

```json
{
  "url": "example.com",
  "websiteName": "Example Website",
  "lastUpdated": "2024-04-21",
  "overallRisk": "medium",
  "overallSummary": "This privacy policy is fairly standard but has some concerning elements regarding data sharing with third parties and unclear data retention policies.",
  "userLocation": "United States",
  "relevantRegulations": ["GDPR", "CCPA"],
  "sections": [
    {
      "title": "Data Collection",
      "summary": "Collects standard and some sensitive personal information",
      "details": "This website collects standard information such as your name, email, and device information. It also collects more sensitive data including browsing history and potentially location data when using certain features.",
      "riskLevel": "medium"
    },
    {
      "title": "Data Usage",
      "summary": "Uses data for service improvement and personalized marketing",
      "details": "Your data is used to improve the service and personalize your experience. It is also used for targeted marketing both on this platform and through third-party advertising networks.",
      "riskLevel": "medium"
    },
    {
      "title": "Data Sharing",
      "summary": "Shares data with numerous third parties",
      "details": "Your information is shared with service providers, advertisers, and analytics companies. Some data may be sold to data brokers, though they claim this is anonymized.",
      "riskLevel": "high"
    }
  ]
}
```

**Error Responses:**
- 400 Bad Request: Invalid URL format
- 404 Not Found: Privacy policy not found for the given URL
- 500 Internal Server Error: Server error during analysis

### User Preferences

#### Get User Preferences

Retrieves the current user's preferences for policy analysis.

```
GET /api/user/preferences
```

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

```json
{
  "country": "United States",
  "riskThreshold": "medium",
  "notifications": true
}
```

**Error Responses:**
- 401 Unauthorized: User not authenticated
- 500 Internal Server Error: Server error

#### Update User Preferences

Updates the user's preferences for policy analysis.

```
POST /api/user/preferences
```

**Request Body:**
```json
{
  "country": "United States",
  "riskThreshold": "medium",
  "notifications": true
}
```

**Request Parameters:**
- `country` (string, required): The user's country of residence
- `riskThreshold` (string, required): The user's preferred risk threshold (one of: "low", "medium", "high")
- `notifications` (boolean, required): Whether the user wants to receive notifications

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

```json
{
  "status": "ok",
  "preferences": {
    "country": "United States",
    "riskThreshold": "medium",
    "notifications": true
  }
}
```

**Error Responses:**
- 400 Bad Request: Invalid parameters
- 401 Unauthorized: User not authenticated
- 500 Internal Server Error: Server error

### User History

#### Get User History

Retrieves the user's policy analysis history.

```
GET /api/user/history
```

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

```json
[
  {
    "url": "https://example.com/privacy-policy",
    "analyzedAt": "2024-04-01T10:05:00Z",
    "policyTitle": "Example Website Privacy Policy",
    "riskLevel": "medium"
  },
  {
    "url": "https://news-site.org/privacy",
    "analyzedAt": "2024-03-30T09:15:00Z",
    "policyTitle": "News Site Privacy",
    "riskLevel": "high"
  }
]
```

**Error Responses:**
- 401 Unauthorized: User not authenticated
- 500 Internal Server Error: Server error

#### Add to History

Adds a policy analysis to the user's history.

```
POST /api/user/history
```

**Request Body:**
```json
{
  "url": "https://example.com/privacy-policy",
  "analyzedAt": "2024-04-01T10:05:00Z",
  "policyTitle": "Example Website Privacy Policy",
  "riskLevel": "medium"
}
```

**Request Parameters:**
- `url` (string, required): The URL of the analyzed policy
- `analyzedAt` (string, required): ISO 8601 timestamp of when the analysis was performed
- `policyTitle` (string, required): The title of the policy
- `riskLevel` (string, required): The overall risk level (one of: "low", "medium", "high")

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

```json
{
  "status": "ok"
}
```

**Error Responses:**
- 400 Bad Request: Invalid parameters
- 401 Unauthorized: User not authenticated
- 500 Internal Server Error: Server error

### Extension Features

#### Check Texting Risk

Checks if a policy has high texting risk.

```
GET /api/extension/texting-risk
```

**Query Parameters:**
- `url` (string, required): The URL of the website to check

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

```json
{
  "url": "example.com",
  "textingRisk": "medium",
  "message": "Texting/SMS marketing appears average. Opt-out is available, but read carefully."
}
```

**Error Responses:**
- 400 Bad Request: Invalid URL
- 404 Not Found: Policy not found
- 500 Internal Server Error: Server error

## Data Models

### PolicyAnalysis

```typescript
interface PolicyAnalysis {
  url: string;
  websiteName: string;
  lastUpdated: string;
  overallRisk: RiskLevel;
  overallSummary: string;
  userLocation: string;
  relevantRegulations: string[];
  sections: PolicySection[];
}

type RiskLevel = 'low' | 'medium' | 'high';

interface PolicySection {
  title: string;
  summary: string;
  details: string;
  riskLevel: RiskLevel;
}
```

### UserPreferences

```typescript
interface UserPreferences {
  country: string;
  riskThreshold: RiskLevel;
  notifications: boolean;
}
```

### HistoryItem

```typescript
interface HistoryItem {
  url: string;
  analyzedAt: string;
  policyTitle: string;
  riskLevel: RiskLevel;
}
```

### TextingRiskResponse

```typescript
interface TextingRiskResponse {
  url: string;
  textingRisk: 'medium' | 'high';
  message: string;
}
```

## Implementation Notes

### Policy Analysis Algorithm

The policy analysis should:
1. Fetch the privacy policy from the given URL
2. Parse the policy text
3. Identify key sections (Data Collection, Data Usage, Data Sharing, etc.)
4. Analyze each section for risk factors
5. Determine overall risk level
6. Generate a summary
7. Identify relevant regulations based on user location

### Risk Assessment

Risk levels are determined by:
- Presence of concerning language (e.g., "we may sell your data")
- Lack of clear opt-out mechanisms
- Broad data collection statements
- Third-party sharing policies
- Data retention policies

### User Preferences Impact

User preferences affect:
- Risk assessment thresholds
- Notification settings
- Regulatory compliance checks based on user location

## Rate Limiting

- 100 requests per minute per IP address
- 1000 requests per hour per authenticated user

## Error Handling

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {} // Optional additional error details
  }
}
```

Common error codes:
- `INVALID_PARAMETERS`: Request parameters are invalid
- `NOT_FOUND`: Requested resource not found
- `UNAUTHORIZED`: Authentication required or failed
- `FORBIDDEN`: User does not have permission
- `INTERNAL_ERROR`: Server error

## Versioning

The API is versioned in the URL path:

```
/api/v1/policies/{url}
```

Current version: v1

## Webhooks

The API supports webhooks for asynchronous policy analysis:

```
POST /api/webhooks/policy-analysis
```

Webhook payload:
```json
{
  "event": "policy.analysis.completed",
  "data": {
    "url": "example.com",
    "analysisId": "analysis_123",
    "status": "completed",
    "result": {} // Full PolicyAnalysis object
  }
}
```

## SDKs and Libraries

Official SDKs are available for:
- JavaScript/TypeScript
- Python
- Java

## Support

For API support, contact:
- Email: api-support@policypal.com
- Documentation: https://docs.policypal.com
- Status page: https://status.policypal.com 