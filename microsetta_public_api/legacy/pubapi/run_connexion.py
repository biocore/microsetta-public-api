import connexion

app = connexion.App(__name__, specification_dir='swagger/')
app.add_api('api.yaml')
app.run(port=8083)
