## English - Telegram Virtual Bank Bot

This is a Telegram bot that simulates a simple virtual bank, allowing users to check their balance, make deposits, and withdraw funds. The bot supports two languages: English and Portuguese.

### How to Use the Repository

#### Requirements

- Python 3.9 or higher
- Virtual environment (optional but recommended)
- Telegram bot token (create a bot using **[BotFather](https://t.me/botfather)**)
- MongoDB database (use MongoDB Atlas or a local MongoDB instance)

#### Instructions

1. Clone the repository:

   ``git clone https://github.com/Andreyspl/TelegramBot``
   ``cd TelegramBot``

2. Create a virtual environment and activate it (optional):

   ``python -m venv venv``
   ``# On Windows``
   ``venv\Scripts\activate``
   ``# On Linux/macOS``
   ``source venv/bin/activate``

3. Install the required dependencies:

   ``pip install -r requirements.txt``

4. Create a `.env` file in the root of the project with the following variables:

   ``TOKEN=<your-telegram-bot-token>``
   ``MONGO_CONN_STRING=<your-mongodb-connection-string>``

   Replace `<your-telegram-bot-token>` with your Telegram bot token and `<your-mongodb-connection-string>` with your MongoDB connection string.

5. Run the bot:

   ``python bot.py``

6. Interact with the bot on Telegram using your own bot, or interact with my bot in the link: **[AndreyBancarioBot](https://t.me/AndreyBancarioBot)**

### Testing the Bot on Telegram

1. Open the Telegram app on your phone or computer.
2. Search for `AndreyBancarioBot` or click the link **https://t.me/AndreyBancarioBot**.
3. Click the **Start** button to begin using the bot.
4. You will be able to:
   - Select your preferred language (English or Portuguese).
   - Check your balance.
   - Make a deposit.
   - Withdraw funds.

### Notes

- All user information, including balance, transactions, and language, is stored in the configured MongoDB database.
- This project was developed for educational purposes and should not be used to store sensitive information or in a production environment.


## Português - Telegram Virtual Bank Bot

Este é um bot do Telegram que simula um banco virtual simples, permitindo que os usuários verifiquem seu saldo, façam depósitos e saques. O bot suporta dois idiomas: inglês e português.

### Como Usar o Repositório

#### Requisitos

- Python 3.9 ou superior
- Ambiente virtual (opcional, mas recomendado)
- Token do bot do Telegram (crie um bot usando **[BotFather](https://t.me/botfather)**)
- Banco de dados MongoDB (use MongoDB Atlas ou uma instância local do MongoDB)

#### Instruções

1. Clone o repositório:

   ``git clone https://github.com/Andreyspl/TelegramBot``
   ``cd TelegramBot``

2. Crie um ambiente virtual e ative-o (opcional):

   ``python -m venv venv``
   ``# No Windows``
   ``venv\Scripts\activate``
   ``# No Linux/macOS``
   ``source venv/bin/activate``

3. Instale as dependências necessárias:

   ``pip install -r requirements.txt``

4. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

   ``TOKEN=<your-telegram-bot-token>``
   ``MONGO_CONN_STRING=<your-mongodb-connection-string>``

   Substitua `<your-telegram-bot-token>` pelo token do seu bot do Telegram e `<your-mongodb-connection-string>` pela string de conexão do seu MongoDB.

5. Execute o bot:

   ``python bot.py``

6. Interaja com o bot no Telegram usando o link dele, ou utilize o meu para testar: **[AndreyBancarioBot](https://t.me/AndreyBancarioBot)**

### Testando o meu Bot no Telegram

1. Abra o aplicativo do Telegram em seu celular ou computador.
2. Procure por `AndreyBancarioBot` ou clique diretamente no link **https://t.me/AndreyBancarioBot**.
3. Clique no botão **Iniciar** para começar a usar o bot.
4. Você poderá:
   - Selecionar seu idioma preferido (Inglês ou Português).
   - Verificar o saldo.
   - Fazer um depósito.
   - Realizar um saque.

### Observações

- Todas as informações dos usuários, incluindo saldo, transações e idioma, são armazenadas no banco de dados MongoDB configurado.
- Este projeto foi desenvolvido para fins educacionais e não deve ser usado para armazenar informações sensíveis ou em produção.
