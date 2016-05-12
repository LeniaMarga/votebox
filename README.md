# votebox
A button voting machine based on a Raspberry Pi.

# Components
A client application running on the Pi posts button presses back to a server application, which stores them in a database (or a file).

# Configurability
The client side has no information on what each button actually means. This is defined on the server side.

# Dependencies
`pip install snowflake`
