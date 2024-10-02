import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

MONGO_CONN_STRING = os.getenv('MONGO_CONN_STRING')
TOKEN = os.getenv('TOKEN')

client = MongoClient(MONGO_CONN_STRING)
db = client['AndreyBancario']
collection = db['usuarios']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user = collection.find_one({'user_id': user_id})

    if not user:
        collection.insert_one({
            'user_id': user_id,
            'balance': 0,
            'last_transaction': None,
            'language': None
        })

    if not user or not user.get('language'):
        keyboard = [
            [
                InlineKeyboardButton("English", callback_data='language_en'),
                InlineKeyboardButton("Português", callback_data='language_pt')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Please select your language / Por favor, selecione seu idioma:', reply_markup=reply_markup)
        return

    language = user['language']
    await show_main_menu(update, context, language)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, language):
    keyboard = [
        [
            InlineKeyboardButton("Check Balance" if language == 'en' else "Ver Saldo", callback_data='check_balance'),
            InlineKeyboardButton("Deposit" if language == 'en' else "Depositar", callback_data='deposit'),
            InlineKeyboardButton("Withdraw" if language == 'en' else "Sacar", callback_data='withdraw'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            'Welcome to Virtual Bank! What would you like to do?' if language == 'en' else 'Bem-vindo ao Banco Virtual! O que você gostaria de fazer?',
            reply_markup=reply_markup
        )
        return

    if update.callback_query:
        await update.callback_query.message.reply_text(
            'Welcome to Virtual Bank! What would you like to do?' if language == 'en' else 'Bem-vindo ao Banco Virtual! O que você gostaria de fazer?',
            reply_markup=reply_markup
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    user = collection.find_one({'user_id': user_id})

    if data == 'language_en':
        collection.update_one({'user_id': user_id}, {'$set': {'language': 'en'}})
        await show_main_menu(update, context, 'en')
        return

    if data == 'language_pt':
        collection.update_one({'user_id': user_id}, {'$set': {'language': 'pt'}})
        await show_main_menu(update, context, 'pt')
        return

    language = user.get('language')

    if data == 'check_balance':
        await check_balance(update, context, language)
        return

    if data == 'deposit':
        context.user_data['action'] = 'deposit'
        await query.message.reply_text(
            'How much would you like to deposit? (Enter a positive integer)' if language == 'en' else 'Quanto você deseja depositar? (Digite um número inteiro maior que 0)'
        )
        return

    if data == 'withdraw':
        context.user_data['action'] = 'withdraw'
        await query.message.reply_text(
            'How much would you like to withdraw? (Enter a positive integer)' if language == 'en' else 'Quanto você deseja sacar? (Digite um número inteiro maior que 0)'
        )
        return

    if data == 'confirm':
        await confirm_transaction(update, context)
        return

    if data == 'cancel':
        await query.message.reply_text('Transaction cancelled.' if language == 'en' else 'Transação cancelada.')
        await show_main_menu(update, context, language)

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE, language):
    user_id = update.effective_user.id
    user = collection.find_one({'user_id': user_id})
    balance = user['balance']
    last_transaction = user.get('last_transaction')

    message = f"Your balance is: $ {balance}" if language == 'en' else f"Seu saldo é: R$ {balance}"
    if last_transaction:
        transaction_time = datetime.fromisoformat(last_transaction['time']).strftime('%d/%m/%Y %H:%M:%S')
        amount = last_transaction['amount']
        trans_type = last_transaction['type']
        message += f"\nLast transaction: {trans_type} of $ {amount} on {transaction_time}" if language == 'en' else f"\nÚltima transação: {trans_type} de R$ {amount} em {transaction_time}"

    await update.callback_query.message.reply_text(message)
    await show_main_menu(update, context, language)

async def confirm_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    amount = context.user_data.get('amount')
    user_id = update.effective_user.id

    user = collection.find_one({'user_id': user_id})
    balance = user['balance']
    language = user.get('language')

    if action == 'withdraw' and amount > balance:
        await update.callback_query.message.reply_text(
            'Insufficient balance for this withdrawal.' if language == 'en' else 'Saldo insuficiente para essa retirada.'
        )
        await show_main_menu(update, context, language)
        return

    new_balance = balance + amount if action == 'deposit' else balance - amount
    trans_type = 'Deposit' if language == 'en' else 'Depósito' if action == 'deposit' else 'Withdrawal' if language == 'en' else 'Saque'

    collection.update_one(
        {'user_id': user_id},
        {'$set': {
            'balance': new_balance,
            'last_transaction': {
                'type': trans_type,
                'amount': amount,
                'time': datetime.now().isoformat()
            }
        }}
    )

    await update.callback_query.message.reply_text(
        f'Transaction of {trans_type.lower()} of $ {amount} completed successfully! Your new balance is $ {new_balance}.' if language == 'en' else f'Transação de {trans_type.lower()} de R$ {amount} realizada com sucesso! Seu novo saldo é R$ {new_balance}.'
    )

    context.user_data.clear()
    await show_main_menu(update, context, language)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    user_id = update.effective_user.id
    user = collection.find_one({'user_id': user_id})
    language = user.get('language')

    if action in ['deposit', 'withdraw']:
        text = update.message.text
        try:
            amount = int(text)
            if amount <= 0:
                raise ValueError
            context.user_data['amount'] = amount

            keyboard = [
                [
                    InlineKeyboardButton("Confirm" if language == 'en' else "Confirmar", callback_data='confirm'),
                    InlineKeyboardButton("Cancel" if language == 'en' else "Cancelar", callback_data='cancel'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f'Do you confirm the transaction of $ {amount}?' if language == 'en' else f'Você confirma a transação de R$ {amount}?',
                reply_markup=reply_markup
            )
        except ValueError:
            await update.message.reply_text(
                'Please enter a positive integer.' if language == 'en' else 'Por favor, digite um número inteiro maior que 0.'
            )
        return

    await update.message.reply_text(
        'Please choose an option from the menu.' if language == 'en' else 'Por favor, escolha uma opção no menu.'
    )

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
