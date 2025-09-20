import { useState } from "react";
import { X, Send, Bot, User } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface AIChatProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  id: number;
  type: "user" | "assistant";
  content: string;
}

const AIChat = ({ isOpen, onClose }: AIChatProps) => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: "assistant",
      content: "Hi! I'm your AI startup analyst. I can help you understand the investment analysis, discuss specific risks, or answer questions about the startup. What would you like to know?"
    }
  ]);

  const suggestedQuestions = [
    "What are the biggest red flags?",
    "How does this compare to competitors?",
    "What's the market size potential?",
    "Should we proceed with investment?"
  ];

  const handleSend = () => {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      type: "user",
      content: message
    };

    const assistantMessage: Message = {
      id: messages.length + 2,
      type: "assistant",
      content: "Based on my analysis of NeuralFlow AI, I can provide detailed insights. This is a demo response - in a real implementation, this would connect to an AI service to provide comprehensive answers about the startup's investment potential, market position, and risk factors."
    };

    setMessages([...messages, userMessage, assistantMessage]);
    setMessage("");
  };

  const handleSuggestedQuestion = (question: string) => {
    setMessage(question);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end p-6">
      <Card className="w-96 h-[500px] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">AI Analyst</h3>
              <p className="text-xs text-muted-foreground">Investment Intelligence</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex items-start space-x-2 max-w-[80%] ${msg.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                  msg.type === 'user' ? 'bg-primary' : 'bg-secondary'
                }`}>
                  {msg.type === 'user' ? (
                    <User className="w-3 h-3 text-primary-foreground" />
                  ) : (
                    <Bot className="w-3 h-3 text-foreground" />
                  )}
                </div>
                <div className={`px-3 py-2 rounded-lg text-sm ${
                  msg.type === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-secondary text-foreground'
                }`}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Suggested Questions */}
        {messages.length <= 1 && (
          <div className="p-4 border-t border-border">
            <p className="text-xs text-muted-foreground mb-2">Suggested questions:</p>
            <div className="space-y-1">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="block w-full text-left text-xs text-primary hover:text-primary/80 p-1 rounded hover:bg-primary-soft transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-border">
          <div className="flex space-x-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask me anything about this startup..."
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              className="flex-1"
            />
            <Button size="sm" onClick={handleSend}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AIChat;