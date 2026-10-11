import { useState, useRef, useEffect } from 'react';
import { Send, Gavel, FileText, Scale, Loader2 } from 'lucide-react';
import './App.css';

// ------------------------------------------------------------------
// 1. WIDGETS GERATIVOS (Design Premium AG-UI)
// ------------------------------------------------------------------
const DocumentoLegalWidget = ({ titulo, data, conteudo }: any) => (
  <div style={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', margin: '12px 0' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
      <div style={{ backgroundColor: '#eff6ff', padding: '10px', borderRadius: '8px', color: '#2563eb' }}>
        <FileText size={20} />
      </div>
      <div>
        <h3 style={{ margin: 0, fontSize: '15px', color: '#111827', fontWeight: 600 }}>{titulo}</h3>
        <span style={{ fontSize: '12px', color: '#6b7280', fontWeight: 500 }}>Válido desde: {data}</span>
      </div>
    </div>
    <p style={{ margin: 0, fontSize: '14px', color: '#4b5563', lineHeight: '1.6' }}>{conteudo}</p>
  </div>
);

const TabelaValoresWidget = ({ itens }: any) => (
  <div style={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden', margin: '12px 0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
      <Scale size={18} color="#4b5563" />
      <h3 style={{ margin: 0, fontSize: '14px', color: '#374151', fontWeight: 600 }}>Tabela de Valores Aplicáveis</h3>
    </div>
    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
      <tbody>
        {itens.map((item: any, i: number) => (
          <tr key={i} style={{ borderBottom: i !== itens.length - 1 ? '1px solid #e5e7eb' : 'none' }}>
            <td style={{ padding: '12px 16px', color: '#4b5563' }}>{item.descricao}</td>
            <td style={{ padding: '12px 16px', color: '#111827', fontWeight: 600, width: '120px' }}>{item.valor} €</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// ------------------------------------------------------------------
// 2. O MOTOR DE CHAT MINIMALISTA
// ------------------------------------------------------------------
export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Faz scroll automático para a mensagem mais recente
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const newMessages = [...messages, { role: "user", text: input }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/ag-ui-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input })
      });
      const data = await response.json();
      setMessages([...newMessages, data]);
    } catch (error) {
      setMessages([...newMessages, { role: "ai", text: "Erro: Backend Python não está a correr na porta 8000." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: '100vh', width: '100vw', backgroundColor: '#ffffff', fontFamily: 'Inter, system-ui, sans-serif', display: 'flex', flexDirection: 'column' }}>
      
      {/* Zona de Chat Centralizada */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '2rem 1rem 8rem 1rem' }}>
        <div style={{ maxWidth: '768px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: '10vh' }}>
              <div style={{ display: 'inline-flex', backgroundColor: '#f3f4f6', padding: '16px', borderRadius: '50%', marginBottom: '16px' }}>
                <Gavel size={32} color="#4b5563" />
              </div>
              <h2 style={{ fontSize: '24px', color: '#111827', margin: '0 0 8px 0' }}>Como posso ajudar com a sua pesquisa jurídica?</h2>
              <p style={{ color: '#6b7280', fontSize: '15px' }}>O Spiderthrone pesquisa jurisprudência e exibe resultados estruturados.</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} style={{ display: 'flex', gap: '16px', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
              
              {/* Avatar da IA */}
              {msg.role === 'ai' && (
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid #e5e7eb' }}>
                  <Gavel size={18} color="#374151" />
                </div>
              )}

              <div style={{ maxWidth: '85%', display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                
                {/* Balão de Texto */}
                {msg.text && (
                  <div style={{ padding: '12px 16px', borderRadius: '20px', backgroundColor: msg.role === 'user' ? '#f3f4f6' : 'transparent', color: '#111827', fontSize: '15px', lineHeight: '1.6', border: msg.role === 'ai' ? 'none' : '1px solid transparent' }}>
                    {msg.text}
                  </div>
                )}

                {/* Renderização Mágica dos Widgets */}
                <div style={{ width: '100%' }}>
                  {msg.widget === 'mostrar_documento_legal' && <DocumentoLegalWidget {...msg.widgetArgs} />}
                  {msg.widget === 'mostrar_tabela_valores' && <TabelaValoresWidget {...msg.widgetArgs} />}
                </div>

              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', gap: '16px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid #e5e7eb' }}>
                <Loader2 size={18} color="#374151" className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              </div>
              <div style={{ padding: '6px 0', color: '#6b7280', fontSize: '14px' }}>A consultar o Qdrant e a gerar resposta...</div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Flutuante Estilo Vercel/ChatGPT */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '24px 16px', background: 'linear-gradient(to top, rgba(255,255,255,1) 60%, rgba(255,255,255,0))' }}>
        <div style={{ maxWidth: '768px', margin: '0 auto', position: 'relative' }}>
          <input 
            type="text" 
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ex: Quais são os valores da injunção?"
            style={{ width: '100%', padding: '16px 56px 16px 24px', borderRadius: '32px', border: '1px solid #e5e7eb', fontSize: '15px', outline: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', backgroundColor: '#f9fafb', boxSizing: 'border-box' }}
          />
          <button 
            onClick={sendMessage} 
            disabled={loading || !input.trim()}
            style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', width: '36px', height: '36px', borderRadius: '50%', backgroundColor: loading || !input.trim() ? '#e5e7eb' : '#111827', color: 'white', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: loading || !input.trim() ? 'default' : 'pointer', transition: 'background-color 0.2s' }}>
            <Send size={16} style={{ marginLeft: '2px' }} />
          </button>
        </div>
        <p style={{ textAlign: 'center', fontSize: '12px', color: '#9ca3af', margin: '12px 0 0 0' }}>
          Spiderthrone Legal RAG • Respostas baseadas em jurisprudência e legislação nacional.
        </p>
      </div>

    </div>
  );
}