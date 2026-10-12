import { useState, useRef, useEffect } from 'react';
import { Send, Gavel, FileText, Scale, Loader2, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

// ------------------------------------------------------------------
// 1. WIDGETS GERATIVOS (Design Premium AG-UI)
// ------------------------------------------------------------------
const DocumentoLegalWidget = ({ titulo, data, conteudo, fonte = "Base de Dados Oficial" }: any) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(`${titulo}\n\n${conteudo}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', margin: '12px 0', position: 'relative' }}>
      
      {/* Botão de Copiar */}
      <button 
        onClick={handleCopy}
        title="Copiar texto"
        style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: '1px solid #e5e7eb', cursor: 'pointer', color: copied ? '#10b981' : '#9ca3af', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '6px', borderRadius: '6px', transition: 'all 0.2s', backgroundColor: copied ? '#ecfdf5' : 'white' }}
      >
        {copied ? <Check size={16} /> : <Copy size={16} />}
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px', paddingRight: '40px' }}>
        <div style={{ backgroundColor: '#eff6ff', padding: '10px', borderRadius: '8px', color: '#2563eb' }}>
          <FileText size={20} />
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '15px', color: '#111827', fontWeight: 600 }}>{titulo}</h3>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px' }}>
            <span style={{ fontSize: '12px', color: '#6b7280', fontWeight: 500 }}>Válido desde: {data}</span>
            <span style={{ fontSize: '11px', backgroundColor: '#f3f4f6', color: '#4b5563', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>{fonte}</span>
          </div>
        </div>
      </div>
      <p style={{ margin: 0, fontSize: '14px', color: '#4b5563', lineHeight: '1.6', whiteSpace: 'pre-wrap', textAlign: 'left' }}>{conteudo}</p>
    </div>
  );
};

const TabelaValoresWidget = ({ itens }: any) => {
  const total = itens?.reduce((acc: number, item: any) => acc + (Number(item.valor) || 0), 0) || 0;

  return (
    <div style={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden', margin: '12px 0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
        <Scale size={18} color="#4b5563" />
        <h3 style={{ margin: 0, fontSize: '14px', color: '#374151', fontWeight: 600 }}>Tabela de Valores Aplicáveis</h3>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
        <tbody>
          {itens?.map((item: any, i: number) => (
            <tr key={i} style={{ borderBottom: '1px solid #e5e7eb' }}>
              <td style={{ padding: '12px 16px', color: '#4b5563', textAlign: 'left' }}>{item.descricao}</td>
              <td style={{ padding: '12px 16px', color: '#111827', fontWeight: 600, width: '120px', textAlign: 'left' }}>{item.valor} €</td>
            </tr>
          ))}
          <tr style={{ backgroundColor: '#f3f4f6' }}>
            <td style={{ padding: '12px 16px', color: '#111827', fontWeight: 600, textAlign: 'right' }}>Total Estimado:</td>
            <td style={{ padding: '12px 16px', color: '#2563eb', fontWeight: 700, textAlign: 'left' }}>{total.toFixed(2)} €</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

// ------------------------------------------------------------------
// 2. O MOTOR DE CHAT RESPONSIVO E FLUIDO
// ------------------------------------------------------------------
export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("A preparar pesquisa...");
  
  const [sessionId] = useState(() => crypto.randomUUID());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (loading) {
      const texts = [
        "A analisar a sua questão jurídica...",
        "A isolar os códigos aplicáveis...",
        "A cruzar jurisprudência e prazos...",
        "A redigir a fundamentação legal..."
      ];
      let i = 0;
      setLoadingText(texts[0]);
      interval = setInterval(() => {
        i = (i + 1) % texts.length;
        setLoadingText(texts[i]);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: "user", text: input };
    const updatedMessages = [...messages, userMessage];
    
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/ag-ui-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: input,
          session_id: sessionId
        })
      });
      const data = __importData(await response.json());
      setMessages([...updatedMessages, data]);
    } catch (error) {
      setMessages([...updatedMessages, { role: "ai", text: "Erro de comunicação com o servidor de RAG." }]);
    } finally {
      setLoading(false);
    }
  };

  function __importData(data: any) {
    return data;
  }

  return (
    <div style={{ height: '100vh', width: '100vw', backgroundColor: '#ffffff', fontFamily: 'Inter, system-ui, sans-serif', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      
      {/* Zona de Mensagens (Ocupa o espaço disponível com scroll independente) */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '2rem 2rem 2rem 2rem', width: '100%', boxSizing: 'border-box' }}>
        <div style={{ width: '100%', maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: '15vh' }}>
              <div style={{ display: 'inline-flex', backgroundColor: '#f3f4f6', padding: '16px', borderRadius: '50%', marginBottom: '16px' }}>
                <Gavel size={32} color="#4b5563" />
              </div>
              <h2 style={{ fontSize: '26px', color: '#111827', margin: '0 0 8px 0', fontWeight: 700 }}>Assistente Jurídico Spiderthrone</h2>
              <p style={{ color: '#6b7280', fontSize: '15px' }}>Legislação em vigor, pesquisa cega a alucinações e widgets gerativos.</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} style={{ display: 'flex', gap: '16px', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', width: '100%' }}>
              
              {msg.role === 'ai' && (
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid #e5e7eb' }}>
                  <Gavel size={18} color="#374151" />
                </div>
              )}

              <div style={{ maxWidth: '85%', display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                
                {msg.text && (
                  <div style={{ 
                    padding: '12px 18px', 
                    borderRadius: '16px', 
                    backgroundColor: msg.role === 'user' ? '#f3f4f6' : 'transparent', 
                    color: '#111827', 
                    fontSize: '15px', 
                    lineHeight: '1.6', 
                    border: msg.role === 'ai' ? 'none' : '1px solid transparent',
                    width: '100%',
                    overflowX: 'auto',
                    textAlign: 'left'
                  }}>
                    {msg.role === 'ai' ? (
                      <div className="markdown-format">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                      </div>
                    ) : (
                      <span style={{ textAlign: 'left', display: 'block' }}>{msg.text}</span>
                    )}
                  </div>
                )}

                {/* Renderização dos Widgets */}
                <div style={{ width: '100%' }}>
                  {msg.widget === 'mostrar_documento_legal' && <DocumentoLegalWidget {...msg.widgetArgs} />}
                  {msg.widget === 'mostrar_tabela_valores' && <TabelaValoresWidget {...msg.widgetArgs} />}
                </div>

              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center', width: '100%' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: '0', border: '1px solid #e5e7eb' }}>
                <Loader2 size={18} color="#374151" className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              </div>
              <div style={{ color: '#4b5563', fontSize: '14px', fontWeight: 500, fontStyle: 'italic', textAlign: 'left' }}>
                {loadingText}
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Caixa de Input Fixa na Base */}
      <div style={{ width: '100%', padding: '16px 2rem 20px 2rem', background: 'linear-gradient(to top, rgba(255,255,255,1) 80%, rgba(255,255,255,0))', borderTop: '1px solid #f3f4f6', boxSizing: 'border-box', flexShrink: 0 }}>
        <div style={{ width: '100%', maxWidth: '900px', margin: '0 auto', position: 'relative' }}>
          <input 
            type="text" 
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ex: Quais são os prazos de recurso no Processo Civil?"
            style={{ width: '100%', padding: '16px 56px 16px 24px', borderRadius: '32px', border: '1px solid #e5e7eb', fontSize: '15px', outline: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', backgroundColor: '#f9fafb', boxSizing: 'border-box', textAlign: 'left' }}
          />
          <button 
            onClick={sendMessage} 
            disabled={loading || !input.trim()}
            style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', width: '36px', height: '36px', borderRadius: '50%', backgroundColor: loading || !input.trim() ? '#e5e7eb' : '#111827', color: 'white', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: loading || !input.trim() ? 'default' : 'pointer', transition: 'background-color 0.2s' }}>
            <Send size={16} style={{ marginLeft: '2px' }} />
          </button>
        </div>
        <p style={{ textAlign: 'center', fontSize: '12px', color: '#9ca3af', margin: '10px 0 0 0' }}>
          Spiderthrone Legal RAG • Informação gerada por IA. Valide sempre com os diplomas oficiais originais.
        </p>
      </div>

    </div>
  );
}