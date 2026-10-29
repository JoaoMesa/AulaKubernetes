---

# 🚀 Laboratório de Kubernetes: Da Máquina Local à Nuvem Híbrida

**Objetivo:** Sair do zero, criar um cluster Kubernetes local, testar a auto-recuperação e, por fim, simular uma arquitetura de nuvem híbrida.

> ⚠️ **ATENÇÃO:** Em todos os comandos deste guia, usaremos `sudo k3s kubectl`.

---

## 🛠️ Fase 1: O Básico (Comandos e Deploy)

Vamos instalar o cluster e criar a nossa primeira aplicação.

### 1. Instalar o Kubernetes (k3s)

```bash
curl -sfL https://get.k3s.io | sh -
```

Verifique se o nó (sua máquina) está pronto:

```bash
sudo k3s kubectl get nodes
```

### 2. Criar um Deployment (Modo Declarativo)

Vamos criar um gerenciador (Deployment) que garante 3 réplicas do Nginx.

```bash
sudo k3s kubectl create deployment meu-app --image=nginx:latest --replicas=3
```

### 3. Expor e Testar

Exponha a aplicação e veja o resultado:

```bash
sudo k3s kubectl expose deployment meu-app --type=NodePort --port=80
sudo k3s kubectl get services
```

_Anote a porta que apareceu no `PORT(S)` (ex: `80:31218/TCP`) e acesse no navegador: `http://localhost:31218`._

---

## 🔬 Fase 2: Testando Conceito Local (Auto-cura)

Vamos provar que o Deployment mantém o estado desejado.

**1. Simule uma falha:**
Pegue o nome de um dos pods listados abaixo (será algo como `meu-app-xxxxxxxx-xxxxx`):

```bash
sudo k3s kubectl get pods
```

Delete o pod (substitua pelo nome que você copiou):

```bash
sudo k3s kubectl delete pod meu-app-<hash>
```

**2. Observando a mágica:**
Rode o comando com `-w` (watch) para ver em tempo real:

```bash
sudo k3s kubectl get pods -w
```

> 💡 **OBSERVE:** O pod que você deletou entrou em `Terminating` e um **novo pod foi criado automaticamente** em segundos. O Kubernetes percebeu que você queria 3 e recriou o que faltava. (Aperte `Ctrl+C` para sair do watch).

### 🧹 3. LIMPEZA (A Transição)

Agora que já entendemos o básico, vamos apagar o `meu-app` para que a nossa próxima aplicação (a distribuída na nuvem) seja a única a rodar o Nginx no cluster. Isso evita confusão na hora de olhar os pods.

```bash
sudo k3s kubectl delete deployment meu-app
sudo k3s kubectl delete service meu-app
```

_(Verifique com `sudo k3s kubectl get pods` se não sobrou nada)._

---

## ☁️ Fase 3: A Nuvem Híbrida (Simulando a AWS)

Agora, vamos colocar uma réplica da sua aplicação no "datacenter do professor".

### 1. Pegar seus dados de conexão

Pegue o IP da sua máquina e o Token do seu cluster:

```bash
hostname -I
sudo cat /var/lib/rancher/k3s/server/node-token
```

### 2. Contratar a Nuvem

Abra o navegador e acesse o portal do professor: `http://<IP_DO_PROFESSOR>:1961`.
Preencha o seu nome, o IP da sua máquina e o Token. Clique em **Conectar**.

### 3. Verificar a conexão

Rode:

```bash
sudo k3s kubectl get nodes
```

> ⚠️ **ATENÇÃO:** Agora você verá **dois** nós: o seu computador (Control Plane) e um nó com um nome esquisito tipo `2945794d5ccd` ou `worker-seu-nome`. **Anote o nome do nó local e o nome do nó da nuvem**, você precisará deles!

### 4. Deploy Distribuído (O Esqueleto YAML)

Vamos criar uma aplicação com a imagem `nginxdemos/hello`, que mostra o nome do pod que respondeu à requisição.

Crie um arquivo chamado `app-nuvem.yaml` e **preencha os campos em branco**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-distribuida
spec:
  # PREENCHA AQUI: Quantas réplicas queremos? (Coloque 2)
  replicas:
  selector:
    matchLabels:
      app: distribuida
  template:
    metadata:
      labels:
        app: distribuida
    spec:
      # PREENCHA AQUI: Adicione a regra de podAntiAffinity para garantir
      # que os pods NUNCA fiquem na mesma máquina.
      # DICA: Olhe o Slide 5 da sua apresentação teórica!
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values: [distribuida]
              topologyKey: kubernetes.io/hostname
      containers:
        - name: web
          # PREENCHA AQUI: Mude para a imagem que mostra o nome do pod
          image:
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: app-distribuida
spec:
  type: NodePort
  selector:
    app: distribuida
  ports:
    - port: 80
      targetPort: 80
      # PREENCHA AQUI: Fixe a porta externa em 30080 para todos acessarem igual
      nodePort:
```

Aplique o arquivo e veja onde os pods caíram:

```bash
sudo k3s kubectl apply -f app-nuvem.yaml
sudo k3s kubectl get pods -o wide
```

> 💡 **OBSERVE:** Na coluna `NODE`, um pod deve estar no **seu nó local** e o outro no **nó da nuvem**. Anote o nome exato do pod que caiu no seu nó local!

### 5. O Teste de Fogo (Derrubando o Local)

Vamos provar que a nuvem segura a bronca. Vamos simular que o seu datacenter local caiu.

**1. Deixe o terminal observando os pods:**

```bash
sudo k3s kubectl get pods -o wide -w
```

**2. Em outro terminal, isole o seu nó local:** (Use o nome do nó local que você anotou no passo 3)

```bash
sudo k3s kubectl cordon <NOME_DO_SEU_NO_LOCAL>
```

**3. Simule a queda do pod local:** (Use o nome do pod local que você anotou no passo 4)

```bash
sudo k3s kubectl delete pod <NOME_DO_POD_LOCAL>
```

> 💡 **O QUE ACONTECEU?** Olhe para o terminal do `watch`. O pod que você deletou vai tentar renascer, mas vai ficar **`Pending`** (Pendente). O Kubernetes está protegendo a sua regra de `Anti-affinity`: ele prefere deixar o pod pendente a colocar dois pods na nuvem.

### 6. A Prova Final (O Terminal não mente)

Deixe o `curl` rodando em loop para provar que o site não caiu:

```bash
curl -s http://localhost:<SUA_PORTA>
```

> 💡 **OBSERVE:** O terminal vai mostrar o nome do pod da nuvem respondendo. O site **continua no ar**, servido 100% pelo datacenter do professor! (Aperte `Ctrl+C` para parar).

### 7. Restaurando o Ambiente

Para voltar tudo ao normal e o pod `Pending` voltar para a sua máquina:

```bash
sudo k3s kubectl uncordon <NOME_DO_SEU_NO_LOCAL>
```

---

## 🧹 Limpeza Final

Para não sobrecarregar o PC do professor, apague a aplicação da nuvem e destrua o seu cluster local:

```bash
sudo k3s kubectl delete deployment app-distribuida
sudo k3s kubectl delete service app-distribuida
/usr/local/bin/k3s-uninstall.sh
```
