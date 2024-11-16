
TOKEN = '7996909621:AAFOZsRplwWzhtppVlDH6oTJEiOIiVw9vco'  # Replace with your actual bot token
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = '7996909621:AAFOZsRplwWzhtppVlDH6oTJEiOIiVw9vco'  # Replace with your actual bot token


def get_schedule():
    url = "http://str-dhn.sch.b-edu.ru/tochka-rosta/%D0%A0%D0%B5%D0%B6%D0%B8%D0%BC-%D0%B7%D0%B0%D0%BD%D1%8F%D1%82%D0%B8%D0%B9/"
    response = requests.get(url)

    if response.status_code != 200:
        print(f'Failed to retrieve data: {response.status_code}')
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    schedule = {}
    entry_content = soup.find('div', class_='entry-content')

    if not entry_content:
        print('Could not find the entry content on the page.')
        return None

    tables = entry_content.find_all('table')
    for table in tables:
        lab_title_elem = table.find_previous('u')
        lab_title = lab_title_elem.text.strip() if lab_title_elem else 'Unknown laboratory'

        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip the header row
            cells = row.find_all('td')
            if cells:
                for index, cell in enumerate(cells[1:], start=1):  # Skip first cell (numbering)
                    lesson_info = cell.get_text(separator="\n", strip=True)
                    if lesson_info:
                        subject_name = f"{lab_title} ({['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'][index - 1]})"
                        schedule.setdefault(subject_name, []).append(lesson_info)

    print(f'Schedule retrieved successfully: {schedule}')
    return schedule


async def send_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    schedule_data = get_schedule()
    if schedule_data:
        keyboard = [
            [InlineKeyboardButton(subject[:30] + ('...' if len(subject) > 30 else ''),
                                  callback_data=f'subject_{index}')]
            for index, subject in enumerate(schedule_data.keys())
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.message.edit_text('Выберите предмет:', reply_markup=reply_markup)
        else:
            message = await update.message.reply_text('Выберите предмет:', reply_markup=reply_markup)
            context.user_data['last_message_id'] = message.message_id  # Save the message ID

    else:
        if update.callback_query:
            await update.callback_query.message.edit_text('Не удалось получить расписание.')
        else:
            await update.message.reply_text('Не удалось получить расписание.')


async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    schedule_data = get_schedule()
    selected_index = int(query.data.split('_')[1])  # Get the index from the callback data
    subjects_list = list(schedule_data.keys())

    if selected_index < len(subjects_list):
        selected_subject = subjects_list[selected_index]
        lessons = schedule_data[selected_subject]

        formatted_lessons = '\n'.join(lessons)
        response = f'*{selected_subject}:*\n' + formatted_lessons if lessons else 'Нет занятий.'

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Вернуться к расписанию", callback_data='return_to_schedule')]
        ])

        await query.message.edit_text(response, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await query.message.edit_text('Не удалось найти расписание для выбранного предмета.')


async def return_to_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_subjects(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Используй команду /schedule для выбора предмета. 🎉')


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('schedule', send_subjects))
    application.add_handler(CallbackQueryHandler(show_schedule, pattern=r'^subject_\d+$'))
    application.add_handler(CallbackQueryHandler(return_to_schedule, pattern='^return_to_schedule$'))

    application.run_polling()


if __name__ == '__main__':
    main()
