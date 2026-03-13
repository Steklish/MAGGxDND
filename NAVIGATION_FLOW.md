# 🗺️ Navigation & User Flow Documentation

## 📋 Complete User Flow

### 1️⃣ First Time / Logged Out User

```
Opens Website
    ↓
Landing Page (Welcome)
    ↓
[Sign In / Register]
    ↓
Auth Modal
    ↓
✅ Login/Register Success
    ↓
Home Page (Dashboard)
```

### 2️⃣ Returning User (Active Session)

```
Opens Website
    ↓
Check localStorage
    ↓
Token Valid? → YES
    ↓
Home Page (Direct Access)
```

### 3️⃣ Guest User

```
Opens Website
    ↓
Landing Page
    ↓
[Continue as Guest]
    ↓
Home Page (Full Access)
    ↓
⚠️ Guest token expires in 24h
```

---

## 🏠 Home Page Features

### Header Actions
| Button | Action |
|--------|--------|
| **Profile (username)** | → Opens Profile Page |
| **⚔️ Create Session** | → Opens Session Creation Modal |
| **Overview/Characters/Sessions** | → Switch tabs |

### Quick Actions
| Button | Action |
|--------|--------|
| **📝 New Character** | → Opens Character Creation |
| **⚔️ Create Session** | → Opens Session Creation |
| **🎲 Quick Play** | → Coming Soon |
| **📚 Rulebook** | → Coming Soon |

---

## 👤 Profile Page

### Tabs
1. **📊 Overview** - User statistics & quick actions
2. **🎭 Characters** - Manage characters
3. **⚔️ Active Games** - Join/manage sessions
4. **⚙️ Settings** - Account settings

### Overview Statistics
- 📅 Registration Date
- 🎭 Total Characters
- ⚔️ Sessions Played
- ⏱️ Total Play Time
- 🟢 Active Sessions
- 📆 Last Active

### Quick Actions
- Create Character
- Create Session
- View Games
- View Characters

---

## 🎮 Game Flow

### Creating/Joining Session

```
Home Page
    ↓
[Create Session] OR [Join Session]
    ↓
Session Detail Page
    ↓
[Start Game]
    ↓
Game Setup (3 steps)
    1. 🎭 Adventure Preferences
    2. 🧙 Character Selection
    3. ✅ Review & Start
    ↓
Game Layout (Playing)
```

### Game Setup Steps

**Step 1: Adventure Preferences**
- Textarea for wishes
- Quick option buttons:
  - 🏰 Dungeon Crawl
  - 👑 Political Intrigue
  - 🌲 Wilderness Adventure
  - 👻 Horror Mystery
- ✨ Let AI Decide button

**Step 2: Character Selection**
- 📋 Use Existing Character
- 🎨 AI Create Character (with description)
- 🎲 Random Character

**Step 3: Review & Start**
- Summary of choices
- 🚀 Start Adventure button
- Loading animation during generation

---

## 🔄 Navigation States

### Page State Management
```typescript
type Page = 
  | 'landing'
  | 'home'
  | 'profile'
  | 'character-creation'
  | 'session-creation'
  | 'session-detail'
  | 'game-setup'
  | 'game';
```

### State Transitions
```
landing → home (after auth)
home → profile (profile button)
home → character-creation (create char)
home → session-creation (create session)
home → session-detail (view/join session)
session-detail → game-setup (start game)
game-setup → game (complete setup)
any → landing (logout)
```

---

## 🎯 Key Features

### ✅ Authentication
- Username/Password login
- Google OAuth (when configured)
- Discord OAuth (when configured)
- Guest mode (24h access)
- Remember me (30 days)

### ✅ Profile Management
- User statistics
- Character management
- Session history
- Account settings
- Logout

### ✅ Session Management
- Create sessions
- Join sessions
- View session details
- Start game with AI setup
- Leave sessions

### ✅ Game Setup
- Custom adventure preferences
- Character selection/creation
- AI-powered character generation
- Quick options for common scenarios
- "Let AI Decide" for automatic setup

---

## 📱 Responsive Design

All pages are fully responsive:
- ✅ Desktop (1920px+)
- ✅ Laptop (1366px)
- ✅ Tablet (768px)
- ✅ Mobile (375px)

---

## 🎨 UI Components

### Common Elements
- **LoadingPage** - Dice animation with tips
- **Toast** - Notifications
- **AuthModal** - Login/Register
- **CharacterCreation** - Character builder
- **SessionCreation** - Session setup
- **SessionDetail** - Session info
- **GameSetup** - Pre-game configuration
- **GameLayout** - Main game interface

### Animations
- Fade in/out transitions
- Smooth page switches
- Loading animations
- Dice rolling effects
- Button hover effects

---

## 🔐 Access Control

| Page | Guest | Authenticated |
|------|-------|---------------|
| Landing | ✅ Full | ✅ Full |
| Home | ✅ Full | ✅ Full |
| Profile | ✅ Full | ✅ Full |
| Character Creation | ✅ Full | ✅ Full |
| Session Creation | ✅ Full | ✅ Full |
| Game Setup | ✅ Full | ✅ Full |
| Game Layout | ✅ Full | ✅ Full |

**Note:** Guests have full access but data expires in 24h

---

## 📊 Local Storage Keys

```javascript
// Authentication
'access_token'      // JWT token
'userId'            // User ID
'username'          // Username
'is_guest'          // Guest flag
'remember_me'       // Remember me flag

// Session
'currentSessionId'  // Active session ID
'currentPlayerId'   // Player ID in session
'gameStatus'        // Game running status

// UI
'previousPage'      // Last visited page
```

---

## 🚀 Quick Start

### For New Users
1. Open website → Landing Page
2. Click "Get Started" or "Sign In"
3. Register/Login
4. Arrive at Home Page
5. Create character or join session

### For Returning Users
1. Open website → Auto-redirect to Home Page
2. Continue from last session
3. View profile or join game

### For Guests
1. Open website → Landing Page
2. Click "Continue as Guest"
3. Full access for 24 hours
4. Can upgrade to full account anytime

---

**Navigation is fully implemented and working! 🎉**
