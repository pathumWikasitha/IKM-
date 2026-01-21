import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronRight, Zap } from 'lucide-react';

interface MessageBubbleProps {
  role: 'user' | 'bot';
  content: string;
  plan?: string;
  context?: string;
  isLoading?: boolean;
}

export function MessageBubble({ role, content, plan, context, isLoading }: MessageBubbleProps) {
  const [isContextOpen, setIsContextOpen] = React.useState(false);

  if (isLoading) {
    return (
      <div className="flex w-full mt-4 space-x-3 max-w-[85%]">
        <Avatar className="h-8 w-8">
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
        <Card className="p-4 bg-muted/50 rounded-tl-sm">
          <div className="flex items-center space-x-2">
            <span className="animate-pulse">Thinking...</span>
          </div>
        </Card>
      </div>
    );
  }

  const isUser = role === 'user';

  return (
    <div className={`flex w-full mt-4 space-x-3 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse space-x-reverse' : ''}`}>
      <Avatar className="h-8 w-8">
        <AvatarFallback>{isUser ? 'U' : 'AI'}</AvatarFallback>
      </Avatar>

      <div className="flex flex-col space-y-2 w-full">
        {plan && (
           <div className="bg-yellow-50 border border-yellow-100 rounded-lg p-3 text-sm text-yellow-900 mb-1">
             <div className="flex items-center gap-2 font-semibold mb-2">
               <Zap className="h-4 w-4" />
               Query Plan
             </div>
             <pre className="whitespace-pre-wrap font-sans">{plan}</pre>
           </div>
        )}

        <Card className={`p-4 ${isUser ? 'bg-primary text-primary-foreground rounded-tr-sm' : 'bg-muted/50 rounded-tl-sm'}`}>
          <div className="prose dark:prose-invert max-w-none text-sm">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </Card>

        {context && (
          <Collapsible
            open={isContextOpen}
            onOpenChange={setIsContextOpen}
            className="w-full"
          >
            <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:underline cursor-pointer">
              {isContextOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              View Retrieved Context
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-2 p-3 bg-muted rounded-md border text-xs overflow-auto max-h-[200px]">
                <pre className="whitespace-pre-wrap">{context}</pre>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}
      </div>
    </div>
  );
}
