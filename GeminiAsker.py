import os
import google.generativeai as genai
import tkinter as tk
from tkinter import messagebox, font, filedialog
from tkinter import ttk
import json
from datetime import datetime
import pathlib

# Foi utilizado o comando $env:API_KEY = "SUA_CHAVE_AQUI" no terminal do PowerShell para definir a variável de ambiente antes de executar o script.

# Lê a chave API da variável de ambiente API_KEY
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("A variável de ambiente API_KEY não está definida. Por favor, defina a variável com sua chave do Gemini API.")

# Configura o cliente Gemini com a chave API
genai.configure(api_key=API_KEY)

# Instancia o modelo uma vez e reutiliza
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    raise Exception(f"Erro ao inicializar o modelo Gemini: {e}. Verifique se a chave API está correta.")

# Histórico corrente (pode ser salvo/carregado)
current_history = None


def configurar_estilo():
    # Cores
    COR_FUNDO = '#2C2C2C'  # Cinza escuro
    COR_TEXTO = '#FFD700'   # Dourado
    COR_BOTAO = '#4A4A4A'   # Cinza médio
    COR_BOTAO_HOVER = '#5C5C5C'  # Hover (um pouco mais claro)
    COR_TEXTO_ENTRADA = '#FFFFFF'  # Branco

    style = ttk.Style()
    style.configure('Medieval.TButton',
                   background=COR_BOTAO,
                   foreground=COR_TEXTO,
                   padding=10,
                   font=('Palatino', 11))
    
    return COR_FUNDO, COR_TEXTO, COR_BOTAO, COR_BOTAO_HOVER, COR_TEXTO_ENTRADA

def save_conversation(history):
    # Salva a conversa em um arquivo JSON timestamped dentro da pasta 'conversations'
    base_dir = pathlib.Path(__file__).parent
    conv_dir = base_dir / 'conversations'
    conv_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = conv_dir / f'convo_{ts}.json'
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Não interrompe a execução por falha ao salvar, apenas loga no console
        print(f'Falha ao salvar conversa: {e}')


def mostrar_resposta(texto_resposta, history):
    global current_history
    # marca histórico atual como o carregado/ativo
    current_history = history
    janela_resposta = tk.Toplevel()
    janela_resposta.title("A resposta do Lendário Ferreiro Mágico")
    janela_resposta.geometry("600x400")

    # Configurações de estilo
    COR_FUNDO, COR_TEXTO, COR_BOTAO, COR_BOTAO_HOVER, COR_TEXTO_ENTRADA = configurar_estilo()
    janela_resposta.configure(bg=COR_FUNDO)

    # Frame para alinhar texto + barra de rolagem
    frame = tk.Frame(janela_resposta, bg=COR_FUNDO)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    # Caixa de texto com rolagem
    texto = tk.Text(frame, 
                   wrap="word",
                   bg=COR_FUNDO,
                   fg=COR_TEXTO,
                   font=('Palatino', 12),
                   relief="solid",
                   border=1)

    # Preenche a caixa de texto com o histórico completo
    conv_display = ''
    for item in history:
        if item.get('role') == 'user':
            conv_display += f"Você: {item.get('content')}\n\n"
        else:
            conv_display += f"Shibori: {item.get('content')}\n\n"

    texto.insert(tk.END, conv_display)
    texto.config(state="disabled")  # impede edição
    texto.pack(side=tk.LEFT, expand=True, fill="both")

    # Adiciona barra de rolagem
    scrollbar = tk.Scrollbar(frame, command=texto.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    texto.config(yscrollcommand=scrollbar.set)

    # Área para responder Shibori (entrada + botão enviar)
    resposta_frame = tk.Frame(janela_resposta, bg=COR_FUNDO)
    resposta_frame.pack(fill="x", side=tk.BOTTOM, padx=10, pady=(0,5))

    entrada_label = tk.Label(resposta_frame, text="Responda Shibori:", bg=COR_FUNDO, fg=COR_TEXTO, font=('Palatino', 10, 'bold'))
    entrada_label.pack(side=tk.LEFT, padx=(0,8))

    entrada_resposta = tk.Entry(resposta_frame, width=50, bg=COR_FUNDO, fg=COR_TEXTO_ENTRADA, insertbackground=COR_TEXTO, font=('Palatino', 10))
    entrada_resposta.pack(side=tk.LEFT, expand=True, fill='x')

    enviar_btn = tk.Button(resposta_frame,
                           text="Enviar resposta",
                           bg=COR_BOTAO,
                           fg=COR_TEXTO,
                           activebackground=COR_BOTAO,
                           activeforeground=COR_TEXTO,
                           font=('Palatino', 10, 'bold'),
                           relief='raised',
                           bd=2)
    enviar_btn.pack(side=tk.RIGHT, padx=(8,0))

    # Barra de botões (fechar) na parte inferior, alinhado à direita
    footer = tk.Frame(janela_resposta, bg=COR_FUNDO)
    footer.pack(fill="x", side=tk.BOTTOM, padx=10, pady=(0,10))

    fechar_btn = tk.Button(footer,
                           text="Obrigado, Shibori.",
                           command=janela_resposta.destroy,
                           bg=COR_BOTAO,
                           fg=COR_TEXTO,
                           activebackground=COR_BOTAO,
                           activeforeground=COR_TEXTO,
                           font=('Palatino', 11, 'bold'),
                           relief='raised',
                           bd=2)
    # posiciona à direita
    fechar_btn.pack(side=tk.RIGHT)

    # Salva a conversa atual ao abrir a janela de resposta
    try:
        save_conversation(history)
    except Exception:
        pass

    # Função para enviar resposta do usuário e obter nova resposta do modelo
    def enviar_resposta():
        user_text = entrada_resposta.get().strip()
        if not user_text:
            messagebox.showwarning("Aviso", "Digite sua resposta para Shibori antes de enviar.")
            return
        # adiciona mensagem do usuário ao histórico
        history.append({"role": "user", "content": user_text})

        # Constrói prompt encadeado com a resposta anterior do modelo
        # monta prompt a partir de todo o histórico para coerência
        conv_prompt = ''
        for item in history:
            if item.get('role') == 'user':
                conv_prompt += f"Usuário: {item.get('content')}\n"
            else:
                conv_prompt += f"Shibori: {item.get('content')}\n"
        conv_prompt += "Responda como Shibori, mantendo o tom sábio, misterioso e com humor antigo."

        prompt = conv_prompt

        try:
            novo_result = model.generate_content(prompt)
            novo_texto = getattr(novo_result, 'text', str(novo_result))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar a resposta: {e}")
            return

        # Anexa a nova resposta à caixa de texto e rola para o fim
        texto.config(state='normal')
        texto.insert(tk.END, "\n\nShibori responde novamente:\n")
        texto.insert(tk.END, novo_texto)
        texto.config(state='disabled')
        texto.see(tk.END)

        # Limpa campo de entrada
        entrada_resposta.delete(0, tk.END)
        # adiciona resposta do modelo ao histórico e salva
        history.append({"role": "assistant", "content": novo_texto})
        try:
            save_conversation(history)
        except Exception:
            pass

    # Vincula o botão enviar e adiciona hover
    enviar_btn.config(command=enviar_resposta)

    def on_enter_btn(e):
        enviar_btn.config(bg=COR_BOTAO_HOVER)

    def on_leave_btn(e):
        enviar_btn.config(bg=COR_BOTAO)

    enviar_btn.bind("<Enter>", on_enter_btn)
    enviar_btn.bind("<Leave>", on_leave_btn)

    # Efeito hover para o botão fechar
    def on_enter_close(e):
        fechar_btn.config(bg=COR_BOTAO_HOVER)

    def on_leave_close(e):
        fechar_btn.config(bg=COR_BOTAO)

    fechar_btn.bind("<Enter>", on_enter_close)
    fechar_btn.bind("<Leave>", on_leave_close)


def armazenar_pergunta():
    pergunta = entrada.get()
    if pergunta.strip() == "":
        messagebox.showwarning("Aviso", "Você entra na forja ancestral e encontra o lendário ferreiro mágico, ele te olha nos olhos e pergunta: Quem é você e o que deseja de mim?")
        return

    # Gera o texto chamando o modelo com a pergunta do usuário
    prompt = (
        f"Você é um lendário ferreiro mágico medieval chamado Shibori, um homem de poucas palavras, mas muito conhecimento e uma pessoa entra em sua forja, você pergunta qual é o nome dessa pessoa e o que ela quer de você, essa pessoa diz: {pergunta}. "
        "Responda de forma sábia, misteriosa e com um toque de humor antigo."
    )

    try:
        resultado = model.generate_content(prompt)
        # O objeto retornado costuma expor o texto em .text; caia para str() se não existir
        resposta_texto = getattr(resultado, "text", str(resultado))
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar a resposta: {e}")
        return

    # Cria histórico inicial: usuário -> modelo
    history = [
        {"role": "user", "content": pergunta},
        {"role": "assistant", "content": resposta_texto}
    ]

    # Salva a conversa inicial
    save_conversation(history)

    # Mostra a resposta gerada com histórico completo
    mostrar_resposta(resposta_texto, history)
    # Limpa o campo para nova pergunta
    entrada.delete(0, tk.END)


# Criação da janela principal
janela = tk.Tk()
janela.title("O Lendário Ferreiro Mágico")
janela.geometry("600x400")

# Configurar o estilo
COR_FUNDO, COR_TEXTO, COR_BOTAO, COR_BOTAO_HOVER, COR_TEXTO_ENTRADA = configurar_estilo()
janela.configure(bg=COR_FUNDO)

# Mensagem fixa acima da entrada (contexto da forja)
fonte_forja = font.Font(family='Palatino', size=11)
mensagem_forja = tk.Label(janela,
                         text=("Você entra na forja ancestral e encontra o lendário ferreiro mágico Shibori, "
                               "ele te olha nos olhos e pergunta: Quem é você e o que deseja de mim?"),
                         font=fonte_forja,
                         wraplength=560,
                         justify='center',
                         bg=COR_FUNDO,
                         fg=COR_TEXTO)
mensagem_forja.pack(pady=(15,5))

# Rótulo com fonte medieval (instrução de input)
fonte_medieval = font.Font(family='Palatino', size=12, weight='bold')
rotulo = tk.Label(janela, 
                 text="Digite sua resposta ao Grande Ferreiro:", 
                 font=fonte_medieval,
                 bg=COR_FUNDO,
                 fg=COR_TEXTO)
rotulo.pack(pady=(5,12))

# Campo de entrada estilizado
entrada = tk.Entry(janela, 
                  width=70,
                  font=('Palatino', 11),
                  bg=COR_FUNDO,
                  fg=COR_TEXTO_ENTRADA,
                  insertbackground=COR_TEXTO)  # Cursor
entrada.pack(pady=10)

# Botão estilizado (uso de tk.Button para garantir controle de cores)
botao = tk.Button(janela,
                  text="🗨 Essa é minha resposta",
                  command=armazenar_pergunta,
                  bg=COR_BOTAO,
                  fg=COR_TEXTO,
                  activebackground=COR_BOTAO,
                  activeforeground=COR_TEXTO,
                  font=('Palatino', 11, 'bold'),
                  relief='raised',
                  bd=2)
botao.pack(pady=20)

# Frame para botões adicionais (save/load)
controls_frame = tk.Frame(janela, bg=COR_FUNDO)
controls_frame.pack(pady=(0,10))

def save_current():
    if not current_history:
        messagebox.showwarning("Aviso", "Não há conversa ativa para salvar.")
        return
    try:
        save_conversation(current_history)
        messagebox.showinfo("Salvo", "Conversa salva em 'conversations' com timestamp.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao salvar conversa: {e}")

def load_conversation():
    base_dir = pathlib.Path(__file__).parent
    conv_dir = base_dir / 'conversations'
    conv_dir.mkdir(exist_ok=True)
    filename = filedialog.askopenfilename(title='Carregar conversa', initialdir=str(conv_dir), filetypes=[('JSON files','*.json')])
    if not filename:
        return
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao carregar arquivo: {e}")
        return
    # Atualiza histórico corrente e abre a janela de resposta com o histórico carregado
    global current_history
    current_history = loaded
    # encontra a última mensagem do assistant para usar como texto_resposta inicial
    last_assistant = None
    for item in reversed(loaded):
        if item.get('role') == 'assistant':
            last_assistant = item.get('content')
            break
    if not last_assistant:
        last_assistant = ''
    mostrar_resposta(last_assistant, current_history)

save_btn = tk.Button(controls_frame, text='💾 Salvar conversa', command=save_current, bg=COR_BOTAO, fg=COR_TEXTO, font=('Palatino', 10), relief='raised', bd=2)
save_btn.pack(side=tk.LEFT, padx=6)

load_btn = tk.Button(controls_frame, text='📂 Carregar conversa', command=load_conversation, bg=COR_BOTAO, fg=COR_TEXTO, font=('Palatino', 10), relief='raised', bd=2)
load_btn.pack(side=tk.LEFT, padx=6)

# hover for save/load
def bind_hover(widget):
    def on_enter(e):
        widget.config(bg=COR_BOTAO_HOVER)
    def on_leave(e):
        widget.config(bg=COR_BOTAO)
    widget.bind('<Enter>', on_enter)
    widget.bind('<Leave>', on_leave)

bind_hover(save_btn)
bind_hover(load_btn)

# Efeito hover para o botão principal
def on_enter_main(e):
    botao.config(bg=COR_BOTAO_HOVER)

def on_leave_main(e):
    botao.config(bg=COR_BOTAO)

botao.bind("<Enter>", on_enter_main)
botao.bind("<Leave>", on_leave_main)

# Inicia o loop da interface
janela.mainloop()
