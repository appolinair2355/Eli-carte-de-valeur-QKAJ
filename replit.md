# Yikik - Telegram Bot for Card Prediction

## Overview

This is a Telegram bot that predicts card suits (♠️, ❤️, ♦️, ♣️) using two prediction methods:

1. **Static Rules**: Predefined patterns (e.g., 10♦️ → ♠️) based on 13 exact rules
2. **Intelligent Mode (INTER)**: Machine learning approach that learns from real data and uses Top 2 triggers per suit

The bot monitors a source channel for card data, processes it through prediction algorithms, and sends predictions to a designated prediction channel. It operates on scheduled prediction sessions (1-6h, 9-12h, 15-18h, 21-24h in Benin timezone).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

- **Flask Web Server** (`main.py`): Entry point handling webhooks and HTTP requests
- **Bot Core** (`bot.py`): High-level Telegram API interactions and update delegation
- **Handlers** (`handlers.py`): Command processing and message handling
- **Prediction Engine** (`card_predictor.py`): Core prediction logic with static rules and intelligent learning
- **Configuration** (`config.py`): Environment variables and settings management

### Prediction System Design

**Problem**: Need reliable card suit predictions using both predefined rules and learned patterns.

**Solution**: Dual-mode prediction system
- Static rules for known patterns (13 predefined mappings)
- INTER mode that learns Top 2 triggers per suit from collected data
- Automatic predictions every 20 minutes during active sessions

**Key Features**:
- Timezone-aware scheduling (Africa/Porto-Novo / Benin)
- Session-based prediction windows
- Verification system with status symbols (✅0️⃣, ✅1️⃣, ✅2️⃣, ❌)

### Webhook Architecture

**Problem**: Bot needs to receive Telegram updates in real-time.

**Solution**: Flask webhook endpoint at `/webhook` receives POST requests from Telegram API and delegates processing to the bot handler chain.

### Channel Configuration

The bot uses two channels:
- **Source Channel**: Receives incoming card data (trigger)
- **Prediction Channel**: Bot outputs predictions

Channel IDs are hardcoded in `card_predictor.py` with clearly marked sections for user modification.

## External Dependencies

### Third-Party Services

| Service | Purpose |
|---------|---------|
| Telegram Bot API | Core messaging platform |
| Render.com / Replit | Hosting platforms |

### Python Packages

| Package | Purpose |
|---------|---------|
| Flask | Web framework for webhook handling |
| gunicorn | Production WSGI server |
| requests | HTTP client for Telegram API calls |
| APScheduler | Background task scheduling (cron-based) |
| pytz | Timezone handling (Benin timezone) |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `WEBHOOK_URL` | Public URL for webhook (auto-configured on Replit) |
| `PORT` | Server port (5000 for Replit, 10000 for Render) |
| `ADMIN_ID` | Telegram user ID for admin access |
| `DEBUG` | Enable debug mode (true/false) |

### Deployment Configuration

- **Replit**: Uses port 5000, auto-generates webhook URL
- **Render.com**: Uses port 10000, requires `render.yaml` configuration
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 main:app`