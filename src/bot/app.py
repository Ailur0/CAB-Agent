"""AIOHTTP web server for the Microsoft Teams bot."""

import sys
import os
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils import Config, setup_logging, get_logger
from src.bot.bot import ChangeManagementBot
from src.bot.state import conversation_reference_manager

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create adapter
SETTINGS = BotFrameworkAdapterSettings(
    app_id=Config.MICROSOFT_APP_ID,
    app_password=Config.MICROSOFT_APP_PASSWORD,
)
ADAPTER = BotFrameworkAdapter(SETTINGS)


# Error handler
async def on_error(context, error):
    """
    Handle errors that occur during bot execution.

    Args:
        context: Turn context where the error occurred.
        error: The exception that was raised.
    """
    logger.error(
        "Bot error occurred",
        error=str(error),
        conversation_id=context.activity.conversation.id if context.activity else None,
    )
    
    # Send a message to the user
    await context.send_activity("Sorry, an error occurred. Please try again later.")


ADAPTER.on_turn_error = on_error

# Create bot instance
BOT = ChangeManagementBot()


async def messages(req: Request) -> Response:
    """
    Handle incoming messages from Microsoft Teams.

    Args:
        req: The incoming HTTP request.

    Returns:
        HTTP response.
    """
    # Verify request is from Bot Framework
    if "application/json" in req.headers.get("Content-Type", ""):
        body = await req.json()
    else:
        logger.warning("Received non-JSON request")
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        # Process the incoming activity
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return Response(status=response.status, body=response.body)
        return Response(status=201)
    except Exception as e:
        logger.error("Error processing activity", error=str(e))
        return Response(status=500, text=str(e))


async def notify(req: Request) -> Response:
    """
    Handle proactive notification requests from the backend.

    This endpoint allows the ADK backend to send proactive messages to users.

    Args:
        req: The incoming HTTP request with notification details.

    Returns:
        HTTP response.
    """
    try:
        body = await req.json()
        user_id = body.get("user_id")
        message = body.get("message")

        if not user_id or not message:
            return Response(status=400, text="Missing user_id or message")

        # Retrieve conversation reference from storage
        conversation_reference = conversation_reference_manager.get_reference(user_id)

        if not conversation_reference:
            logger.warning("Conversation reference not found", user_id=user_id)
            return Response(status=404, text="User conversation reference not found")

        logger.info("Sending proactive notification", user_id=user_id, message=message[:50])

        # Send proactive message
        async def callback(turn_context):
            await turn_context.send_activity(message)

        await ADAPTER.continue_conversation(
            conversation_reference,
            callback,
            Config.MICROSOFT_APP_ID,
        )

        return Response(status=200, text="Notification sent successfully")
    except Exception as e:
        logger.error("Error sending notification", error=str(e))
        return Response(status=500, text=str(e))


async def health(req: Request) -> Response:
    """
    Health check endpoint.

    Args:
        req: The incoming HTTP request.

    Returns:
        HTTP response with health status.
    """
    return Response(status=200, text="Bot is running")


def create_app() -> web.Application:
    """
    Create and configure the AIOHTTP application.

    Returns:
        Configured web application.
    """
    app = web.Application()
    
    # Add routes
    app.router.add_post("/api/messages", messages)
    app.router.add_post("/api/notify", notify)
    app.router.add_get("/health", health)
    
    logger.info("AIOHTTP application created")
    return app


if __name__ == "__main__":
    # Validate configuration
    missing_config = Config.validate()
    if missing_config:
        logger.error(
            "Missing required configuration",
            missing_keys=missing_config,
        )
        print("\n❌ ERROR: Missing required configuration:")
        for key in missing_config:
            print(f"   - {key}")
        print("\nPlease check your .env file and ensure all required values are set.")
        print("See .env.template for reference.\n")
        sys.exit(1)

    logger.info(
        "Starting Change Management Bot",
        host=Config.BOT_HOST,
        port=Config.BOT_PORT,
    )
    
    print(f"\n🤖 Change Management Bot Starting...")
    print(f"   Host: {Config.BOT_HOST}")
    print(f"   Port: {Config.BOT_PORT}")
    print(f"   Endpoints:")
    print(f"      - POST /api/messages (Bot Framework)")
    print(f"      - POST /api/notify (Proactive notifications)")
    print(f"      - GET  /health (Health check)")
    print(f"\n   Make sure to:")
    print(f"   1. Run ngrok: ngrok http {Config.BOT_PORT}")
    print(f"   2. Update bot messaging endpoint in Azure Portal")
    print(f"   3. Add bot to Teams for testing\n")

    app = create_app()
    web.run_app(app, host=Config.BOT_HOST, port=Config.BOT_PORT)
