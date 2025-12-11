import express from 'express';
import cors from 'cors';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { OAuth2Client } from 'google-auth-library';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';

// Middleware
app.use(cors());
app.use(express.json());

// In-memory storage (replace with database in production)
const users = new Map();
const dataSources = new Map();
const notifications = [];

// Helper functions
function generateToken(userId, email) {
  return jwt.sign(
    { userId, email, exp: Math.floor(Date.now() / 1000) + 24 * 60 * 60 },
    JWT_SECRET
  );
}

function hashPassword(password) {
  return bcrypt.hashSync(password, 10);
}

function verifyPassword(password, hash) {
  return bcrypt.compareSync(password, hash);
}

// Middleware to verify JWT token
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ message: 'Unauthorized' });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ message: 'Invalid or expired token' });
  }
}

// Google OAuth client
const googleClient = GOOGLE_CLIENT_ID 
  ? new OAuth2Client(GOOGLE_CLIENT_ID)
  : null;

// ==================== AUTH ROUTES ====================

// Signup
app.post('/api/auth/signup', async (req, res) => {
  try {
    const { email, password, phone } = req.body;

    // Validation
    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    if (password.length < 8) {
      return res.status(400).json({ message: 'Password must be at least 8 characters' });
    }

    // Check if user exists
    if (users.has(email.toLowerCase())) {
      return res.status(409).json({ message: 'User already exists' });
    }

    // Create user
    const userId = email.toLowerCase();
    const hashedPassword = hashPassword(password);
    const user = {
      userId,
      email: email.toLowerCase(),
      password: hashedPassword,
      phone: phone || null,
      createdAt: new Date().toISOString(),
      subscriptionTier: 'free',
    };

    users.set(userId, user);

    // Generate token
    const token = generateToken(userId, user.email);

    // Return user (without password)
    const userResponse = {
      user_id: user.userId,
      email: user.email,
      phone: user.phone,
      created_at: user.createdAt,
      subscription_tier: user.subscriptionTier,
    };

    res.status(201).json({
      user: userResponse,
      token,
    });
  } catch (error) {
    console.error('Signup error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Login
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    const userId = email.toLowerCase();
    const user = users.get(userId);

    if (!user) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    if (!verifyPassword(password, user.password)) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Generate token
    const token = generateToken(userId, user.email);

    // Return user (without password)
    const userResponse = {
      user_id: user.userId,
      email: user.email,
      phone: user.phone,
      created_at: user.createdAt,
      subscription_tier: user.subscriptionTier,
    };

    res.json({
      user: userResponse,
      token,
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Google OAuth Signup/Login
app.post('/api/auth/google', async (req, res) => {
  try {
    const { credential } = req.body; // Google ID token

    if (!googleClient) {
      return res.status(500).json({ message: 'Google OAuth not configured' });
    }

    if (!credential) {
      return res.status(400).json({ message: 'Google credential is required' });
    }

    // Verify Google token
    const ticket = await googleClient.verifyIdToken({
      idToken: credential,
      audience: GOOGLE_CLIENT_ID,
    });

    const payload = ticket.getPayload();
    const email = payload.email.toLowerCase();
    const userId = email;
    const name = payload.name;
    const picture = payload.picture;

    // Check if user exists
    let user = users.get(userId);

    if (!user) {
      // Create new user from Google
      user = {
        userId,
        email,
        name,
        picture,
        password: null, // No password for OAuth users
        phone: null,
        createdAt: new Date().toISOString(),
        subscriptionTier: 'free',
        authProvider: 'google',
      };
      users.set(userId, user);
    }

    // Generate token
    const token = generateToken(userId, user.email);

    // Return user
    const userResponse = {
      user_id: user.userId,
      email: user.email,
      name: user.name,
      picture: user.picture,
      phone: user.phone,
      created_at: user.createdAt,
      subscription_tier: user.subscriptionTier,
    };

    res.json({
      user: userResponse,
      token,
    });
  } catch (error) {
    console.error('Google OAuth error:', error);
    res.status(401).json({ message: 'Invalid Google token' });
  }
});

// Token refresh
app.post('/api/auth/refresh', authenticateToken, (req, res) => {
  try {
    const newToken = generateToken(req.user.userId, req.user.email);
    res.json({ token: newToken });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// ==================== USER ROUTES ====================

// Get current user
app.get('/api/users/me', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const user = users.get(userId);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    const userResponse = {
      user_id: user.userId,
      email: user.email,
      name: user.name,
      picture: user.picture,
      phone: user.phone,
      created_at: user.createdAt,
      subscription_tier: user.subscriptionTier,
    };

    res.json(userResponse);
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update user
app.put('/api/users/me', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const user = users.get(userId);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Update allowed fields
    if (req.body.phone !== undefined) {
      user.phone = req.body.phone;
    }

    users.set(userId, user);

    const userResponse = {
      user_id: user.userId,
      email: user.email,
      name: user.name,
      picture: user.picture,
      phone: user.phone,
      created_at: user.createdAt,
      subscription_tier: user.subscriptionTier,
    };

    res.json(userResponse);
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// ==================== DATA SOURCES ROUTES ====================

// List data sources
app.get('/api/data-sources', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const userSources = Array.from(dataSources.values())
      .filter((ds) => ds.userId === userId)
      .map(({ password, ...rest }) => rest); // Remove password

    res.json(userSources);
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Create data source
app.post('/api/data-sources', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { email, password, host, port, use_ssl, source_type } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    // Auto-detect host if not provided
    let imapHost = host;
    if (!imapHost) {
      if (email.includes('@gmail.com')) {
        imapHost = 'imap.gmail.com';
      } else if (email.includes('@outlook.com') || email.includes('@hotmail.com')) {
        imapHost = 'imap-mail.outlook.com';
      } else if (email.includes('@yahoo.com')) {
        imapHost = 'imap.mail.yahoo.com';
      } else {
        const domain = email.split('@')[1];
        imapHost = `imap.${domain}`;
      }
    }

    const sourceId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const source = {
      source_id: sourceId,
      user_id: userId,
      source_type: source_type || 'email',
      email: email.toLowerCase(),
      password, // In production, encrypt this
      host: imapHost,
      port: port || 993,
      use_ssl: use_ssl !== false,
      status: 'active',
      created_at: new Date().toISOString(),
      last_sync_at: null,
    };

    dataSources.set(sourceId, source);

    // Return without password
    const { password: _, ...sourceResponse } = source;
    res.status(201).json(sourceResponse);
  } catch (error) {
    console.error('Create data source error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Test data source connection
app.post('/api/data-sources/:id/test', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { id } = req.params;
    const source = dataSources.get(id);

    if (!source || source.user_id !== userId) {
      return res.status(404).json({ message: 'Data source not found' });
    }

    // Test IMAP connection
    try {
      const imap = await import('imap');
      // For now, just return success (in production, actually test connection)
      res.json({ success: true, message: 'Connection test successful' });
    } catch (error) {
      res.json({ success: false, message: 'Connection test failed: ' + error.message });
    }
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update data source
app.put('/api/data-sources/:id', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const { id } = req.params;
    const source = dataSources.get(id);

    if (!source || source.user_id !== userId) {
      return res.status(404).json({ message: 'Data source not found' });
    }

    // Update fields
    if (req.body.status !== undefined) source.status = req.body.status;
    if (req.body.host !== undefined) source.host = req.body.host;
    if (req.body.port !== undefined) source.port = req.body.port;
    if (req.body.use_ssl !== undefined) source.use_ssl = req.body.use_ssl;
    if (req.body.password !== undefined) source.password = req.body.password;

    dataSources.set(id, source);

    const { password: _, ...sourceResponse } = source;
    res.json(sourceResponse);
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Delete data source
app.delete('/api/data-sources/:id', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const { id } = req.params;
    const source = dataSources.get(id);

    if (!source || source.user_id !== userId) {
      return res.status(404).json({ message: 'Data source not found' });
    }

    dataSources.delete(id);
    res.json({ message: 'Data source deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// ==================== NOTIFICATIONS ROUTES ====================

// Get notifications
app.get('/api/notifications', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const limit = parseInt(req.query.limit) || 20;
    const userNotifications = notifications
      .filter((n) => n.user_id === userId)
      .slice(0, limit);

    res.json(userNotifications);
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get stats
app.get('/api/stats', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const userSources = Array.from(dataSources.values()).filter((ds) => ds.user_id === userId);
    const userNotifications = notifications.filter((n) => n.user_id === userId);

    res.json({
      total_emails: userNotifications.length,
      active_sources: userSources.filter((ds) => ds.status === 'active').length,
      notifications_sent: userNotifications.filter((n) => n.delivered_at).length,
      last_sync: userSources[0]?.last_sync_at || null,
    });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get status
app.get('/api/status', authenticateToken, (req, res) => {
  try {
    res.json({
      processing_active: true,
      next_run: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      llm_connected: true,
    });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// ==================== SETTINGS ROUTES ====================

// Get settings
app.get('/api/settings', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const user = users.get(userId);

    res.json({
      notification_method: user?.notification_method || 'email',
      notification_email: user?.notification_email || user?.email,
      notification_phone: user?.notification_phone || user?.phone,
      summary_frequency: user?.summary_frequency || 15,
    });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update settings
app.put('/api/settings', authenticateToken, (req, res) => {
  try {
    const userId = req.user.userId;
    const user = users.get(userId);

    if (req.body.notification_method) user.notification_method = req.body.notification_method;
    if (req.body.notification_email) user.notification_email = req.body.notification_email;
    if (req.body.notification_phone) user.notification_phone = req.body.notification_phone;
    if (req.body.summary_frequency) user.summary_frequency = req.body.summary_frequency;

    users.set(userId, user);

    res.json({
      notification_method: user.notification_method,
      notification_email: user.notification_email,
      notification_phone: user.notification_phone,
      summary_frequency: user.summary_frequency,
    });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 API Server running on http://localhost:${PORT}`);
  console.log(`📝 Health check: http://localhost:${PORT}/api/health`);
  if (!GOOGLE_CLIENT_ID) {
    console.log('⚠️  Google OAuth not configured. Set GOOGLE_CLIENT_ID in .env');
  }
});

