// ============================================================
// Zayro Teams — MongoDB Setup
// DB: zayro_teams
// Run via mongo_install.sh (credentials passed from environment)
// ============================================================

// Switch to admin to create the user
use("admin");

const MONGO_USER = _getEnv("MONGO_USER") || "vamsi";
const MONGO_PASS = _getEnv("MONGO_PASS");
if (!MONGO_PASS) { throw new Error("MONGO_PASS env var is required"); }

// Create admin-level user
db.createUser({
  user: MONGO_USER,
  pwd: MONGO_PASS,
  roles: [
    { role: "userAdminAnyDatabase", db: "admin" },
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
});

print("✓ User '" + MONGO_USER + "' created in admin");

// Switch to project database
use("zayro_teams");

db.createUser({
  user: MONGO_USER,
  pwd: MONGO_PASS,
  roles: [{ role: "readWrite", db: "zayro_teams" }]
});

print("✓ User 'vamsi' granted readWrite on zayro_teams");

// ── Auto-create collections with validators ──────────────────

// users
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "username", "password", "created_at"],
      properties: {
        email:      { bsonType: "string" },
        username:   { bsonType: "string" },
        password:   { bsonType: "string" },
        first_name: { bsonType: "string" },
        last_name:  { bsonType: "string" },
        avatar:     { bsonType: ["string", "null"] },
        bio:        { bsonType: "string" },
        is_online:  { bsonType: "bool" },
        is_superuser: { bsonType: "bool" },
        created_at: { bsonType: "date" }
      }
    }
  }
});
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ username: 1 }, { unique: true });
print("✓ Collection 'users' created");

// teams
db.createCollection("teams", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "created_by", "created_at"],
      properties: {
        name:        { bsonType: "string" },
        description: { bsonType: "string" },
        avatar:      { bsonType: ["string", "null"] },
        created_by:  { bsonType: "objectId" },
        created_at:  { bsonType: "date" }
      }
    }
  }
});
db.teams.createIndex({ name: 1 });
print("✓ Collection 'teams' created");

// team_members
db.createCollection("team_members", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["team_id", "user_id", "role", "joined_at"],
      properties: {
        team_id:   { bsonType: "objectId" },
        user_id:   { bsonType: "objectId" },
        role:      { enum: ["admin", "member"] },
        joined_at: { bsonType: "date" }
      }
    }
  }
});
db.team_members.createIndex({ team_id: 1, user_id: 1 }, { unique: true });
print("✓ Collection 'team_members' created");

// channels
db.createCollection("channels", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["team_id", "name", "channel_type", "created_at"],
      properties: {
        team_id:      { bsonType: "objectId" },
        name:         { bsonType: "string" },
        channel_type: { enum: ["text", "voice"] },
        created_at:   { bsonType: "date" }
      }
    }
  }
});
db.channels.createIndex({ team_id: 1 });
print("✓ Collection 'channels' created");

// messages (channel messages)
db.createCollection("messages", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["channel_id", "sender_id", "content", "created_at"],
      properties: {
        channel_id: { bsonType: "objectId" },
        sender_id:  { bsonType: "objectId" },
        content:    { bsonType: "string" },
        created_at: { bsonType: "date" }
      }
    }
  }
});
db.messages.createIndex({ channel_id: 1, created_at: 1 });
print("✓ Collection 'messages' created");

// direct_messages
db.createCollection("direct_messages", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["sender_id", "receiver_id", "content", "created_at"],
      properties: {
        sender_id:   { bsonType: "objectId" },
        receiver_id: { bsonType: "objectId" },
        content:     { bsonType: "string" },
        is_read:     { bsonType: "bool" },
        created_at:  { bsonType: "date" }
      }
    }
  }
});
db.direct_messages.createIndex({ sender_id: 1, receiver_id: 1 });
db.direct_messages.createIndex({ created_at: 1 });
print("✓ Collection 'direct_messages' created");

// invitations
db.createCollection("invitations", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["token", "email", "invited_by", "status", "created_at"],
      properties: {
        token:      { bsonType: "string" },
        email:      { bsonType: "string" },
        invited_by: { bsonType: "objectId" },
        team_id:    { bsonType: ["objectId", "null"] },
        status:     { enum: ["pending", "accepted", "declined"] },
        created_at: { bsonType: "date" },
        expires_at: { bsonType: ["date", "null"] }
      }
    }
  }
});
db.invitations.createIndex({ token: 1 }, { unique: true });
db.invitations.createIndex({ email: 1 });
print("✓ Collection 'invitations' created");

// call_sessions
db.createCollection("call_sessions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["room_id", "call_type", "initiator_id", "status", "started_at"],
      properties: {
        room_id:      { bsonType: "string" },
        call_type:    { enum: ["audio", "video"] },
        initiator_id: { bsonType: "objectId" },
        participants: { bsonType: "array" },
        team_id:      { bsonType: ["objectId", "null"] },
        status:       { enum: ["calling", "active", "ended"] },
        started_at:   { bsonType: "date" },
        ended_at:     { bsonType: ["date", "null"] }
      }
    }
  }
});
db.call_sessions.createIndex({ room_id: 1 }, { unique: true });
print("✓ Collection 'call_sessions' created");

// ── Summary ──────────────────────────────────────────────────
print("");
print("══════════════════════════════════════════");
print("  MongoDB Setup Complete — zayro_teams");
print("══════════════════════════════════════════");
print("  Host     : localhost:27017");
print("  Database : zayro_teams");
print("  User     : vamsi");
print("  Password : zayron@2026");
print("  Collections created:");
print("    • users");
print("    • teams");
print("    • team_members");
print("    • channels");
print("    • messages");
print("    • direct_messages");
print("    • invitations");
print("    • call_sessions");
print("══════════════════════════════════════════");
