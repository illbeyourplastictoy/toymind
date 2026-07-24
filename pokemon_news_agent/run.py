"""Точка входа: запуск Telegram-бота с планировщиком.

    python -m pokemon_news_agent.run
или из папки pokemon_news_agent:
    python run.py
"""

import bot


def main():
    application = bot.build_app()
    print("🃏 Pokemon News Agent запущен. Мониторю рынок и жду апрува...")
    application.run_polling()


if __name__ == "__main__":
    main()
