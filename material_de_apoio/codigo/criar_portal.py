from flask import Flask, request, render_template_string
import subprocess

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>Portal AWS da Sala</title></head>
<body style="font-family: Arial; margin: 40px;">
    <h2>☁️ Portal do Provedor Cloud</h2>
    <p>Preencha os dados do seu cluster local para receber um nó na nuvem.</p>
    <form method="POST" action="/registrar">
        <label>Nome do Aluno:</label><br>
        <input type="text" name="nome" required><br><br>
        
        <label>IP do seu k3s Server:</label><br>
        <input type="text" name="ip" placeholder="ex: 10.42.0.15" required><br><br>
        
        <label>Token do k3s:</label><br>
        <input type="text" name="token" required><br><br>
        
        <input type="submit" value="Conectar meu cluster à Nuvem" style="padding: 10px; font-size: 16px;">
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/registrar', methods=['POST'])
def registrar():
    nome = request.form['nome'].lower().replace(" ", "-")
    ip = request.form['ip']
    token = request.form['token']
    container_name = f"worker-{nome}"
    
    # Remove container antigo se existir
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
    
    # Comando para criar o worker na sua máquina
    comando = [
        "docker", "run", "-d", "--name", container_name, "--privileged",
        "-e", f"K3S_URL=https://{ip}:6443",
        "-e", f"K3S_TOKEN={token}",
        "rancher/k3s:v1.28.2-k3s1", "agent"
    ]
    
    try:
        subprocess.run(comando, check=True, capture_output=True)
        return f"<h3>✅ Sucesso! O nó na nuvem foi criado para {nome}.</h3><p>Volte para o terminal e rode 'kubectl get nodes'.</p>"
    except subprocess.CalledProcessError as e:
        return f"<h3>❌ Erro ao conectar. Verifique o IP e o Token.</h3><pre>{e.stderr.decode()}</pre>"
    except Exception as e:
        return f"<h3>❌ Erro inesperado: {str(e)}</h3>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1961)