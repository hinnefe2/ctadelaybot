import connexion


app = connexion.App(__name__, specification_dir='./')
app.add_api('swagger.yaml')


@app.route('/')
def index():
    return "Hello, world!", 200


# We only need this for local development.
if __name__ == '__main__':
    app.run()
