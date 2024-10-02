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
            'language': None,
            'methods': []  # Lista de métodos de pagamento
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

    if data == 'add_new_method':
        await add_new_method_flow(update, context, language)
        return

    if data.startswith('method_type_'):
        method_type = data.split('_')[-1]
        context.user_data['adding_method_type'] = method_type

        if method_type == 'bank':
            await query.message.reply_text('Please enter the name of the bank:' if language == 'en' else 'Por favor, insira o nome do banco:')
        elif method_type == 'paypal':
            await query.message.reply_text('Please enter your Paypal e-mail address:' if language == 'en' else 'Por favor, insira o endereço de e-mail do Paypal:')
        elif method_type == 'crypto':
            keyboard = [
                [
                    InlineKeyboardButton("BTC", callback_data='crypto_type_btc'),
                    InlineKeyboardButton("ETH", callback_data='crypto_type_eth'),
                    InlineKeyboardButton("USDT", callback_data='crypto_type_usdt')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('Select the cryptocurrency type:' if language == 'en' else 'Selecione o tipo de criptomoeda:', reply_markup=reply_markup)
        return

    if data.startswith('crypto_type_'):
        crypto_type = data.split('_')[-1]
        context.user_data['crypto_type'] = crypto_type
        await query.message.reply_text('Please enter your crypto address:' if language == 'en' else 'Por favor, insira o endereço da criptomoeda:')
        return

    if data.startswith('method_'):
        method_index = int(data.split('_')[-1])
        context.user_data['selected_method'] = method_index
        await confirm_transaction(update, context)
        return

    if data == 'confirm':
        await confirm_transaction(update, context)
        return

    if data == 'cancel':
        await query.message.reply_text('Transaction cancelled.' if language == 'en' else 'Transação cancelada.')
        await show_main_menu(update, context, language)

async def add_new_method_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, language):
    context.user_data['adding_method'] = True
    keyboard = [
        [
            InlineKeyboardButton("Bank Transfer" if language == 'en' else "Transferência Bancária", callback_data='method_type_bank'),
            InlineKeyboardButton("Paypal", callback_data='method_type_paypal'),
            InlineKeyboardButton("Crypto", callback_data='method_type_crypto')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        'Select the type of method:' if language == 'en' else 'Selecione o tipo de método:',
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    user_id = update.effective_user.id
    user = collection.find_one({'user_id': user_id})
    language = user.get('language')

    if context.user_data.get('adding_method'):
        method_type = context.user_data['adding_method_type']
        text = update.message.text.strip()

        new_method = {}
        if method_type == 'bank':
            new_method = {'type': 'Bank Transfer', 'description': f'Bank: {text}'}
        elif method_type == 'paypal':
            new_method = {'type': 'Paypal', 'description': f'Paypal: {text}'}
        elif method_type == 'crypto':
            crypto_type = context.user_data['crypto_type']
            new_method = {'type': crypto_type, 'description': f'Crypto ({crypto_type.upper()}): {text}'}

        # Adiciona o método ao usuário
        collection.update_one(
            {'user_id': user_id},
            {'$push': {'methods': new_method}}
        )

        await update.message.reply_text(
            'Method added successfully!' if language == 'en' else 'Método adicionado com sucesso!',
        )

        # Continua o fluxo de depósito/saque
        context.user_data.pop('adding_method', None)
        context.user_data.pop('adding_method_type', None)
        context.user_data.pop('crypto_type', None)

        methods = collection.find_one({'user_id': user_id}).get('methods', [])
        keyboard = [
            [InlineKeyboardButton(method['description'], callback_data=f'method_{index}') for index, method in enumerate(methods)],
            [InlineKeyboardButton("Cancel" if language == 'en' else "Cancelar", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            'Choose a deposit/withdrawal method:' if language == 'en' else 'Escolha um método de depósito/saque:',
            reply_markup=reply_markup
        )
        return

    if action in ['deposit', 'withdraw']:
        text = update.message.text
        try:
            amount = int(text)
            if amount <= 0:
                raise ValueError
            context.user_data['amount'] = amount

            methods = user.get('methods', [])
            if methods:
                keyboard = [
                    [InlineKeyboardButton(method['description'], callback_data=f'method_{index}') for index, method in enumerate(methods)],
                    [InlineKeyboardButton("Add New Method" if language == 'en' else "Adicionar Novo Método", callback_data='add_new_method')]
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("Add New Method" if language == 'en' else "Adicionar Novo Método", callback_data='add_new_method')]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                'Choose a deposit/withdrawal method:' if language == 'en' else 'Escolha um método de depósito/saque:',
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
        method = last_transaction['method']
        message += f"\nLast transaction: {trans_type} of $ {amount} on {transaction_time} using {method}" if language == 'en' else f"\nÚltima transação: {trans_type} de R$ {amount} em {transaction_time} usando {method}"

    await update.callback_query.message.reply_text(message)
    await show_main_menu(update, context, language)

async def confirm_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    amount = context.user_data.get('amount')
    user_id = update.effective_user.id

    user = collection.find_one({'user_id': user_id})
    balance = user['balance']
    language = user.get('language')
    method_index = context.user_data['selected_method']
    method = user['methods'][method_index]['description']

    if action == 'withdraw' and amount > balance:
        await update.callback_query.message.reply_text(
            'Insufficient balance for this withdrawal.' if language == 'en' else 'Saldo insuficiente para essa retirada.'
        )
        await show_main_menu(update, context, language)
        return

    new_balance = balance + amount if action == 'deposit' else balance - amount
    trans_type = 'Deposit' if action == 'deposit' else 'Withdrawal'

    collection.update_one(
        {'user_id': user_id},
        {'$set': {
            'balance': new_balance,
            'last_transaction': {
                'type': trans_type,
                'amount': amount,
                'method': method,
                'time': datetime.now().isoformat()
            }
        }}
    )

    await update.callback_query.message.reply_text(
        f'Transaction of {trans_type.lower()} of $ {amount} using {method} completed successfully! Your new balance is $ {new_balance}.' if language == 'en' else f'Transação de {trans_type.lower()} de R$ {amount} usando {method} realizada com sucesso! Seu novo saldo é R$ {new_balance}.'
    )

    context.user_data.clear()
    await show_main_menu(update, context, language)

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
