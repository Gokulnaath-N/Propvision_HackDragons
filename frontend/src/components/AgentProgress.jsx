import { useJobStatus } from '../hooks/useJobStatus'

const STAGES = [
  { label: 'Enhancing images',      threshold: 18 },
  { label: 'Classifying rooms',     threshold: 36 },
  { label: 'Scoring quality',       threshold: 54 },
  { label: 'Detecting objects',     threshold: 70 },
  { label: 'Generating embeddings', threshold: 86 },
  { label: 'AI synthesis',          threshold: 100 },
]

export default function AgentProgress({ jobId, onComplete }) {
  const { status, progress, stage, results } = useJobStatus(jobId)

  if (status === 'complete' && onComplete) {
    onComplete(results)
  }

  return (
    <div className="agent-progress max-w-md mx-auto p-6 bg-card rounded-2xl border border-border/50 shadow-sm mt-8">
      
      {/* Progress Bar */}
      <div className="w-full h-2 bg-muted rounded-full overflow-hidden mb-6 relative">
        <div
          className="h-full bg-primary transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="space-y-3">
        {STAGES.map((s, i) => {
            const isDone = progress >= s.threshold;
            const isActive = !isDone && stage === s.label;
            
            return (
          <div
            key={i}
            className={`flex items-center gap-3 text-sm transition-colors ${
              isDone ? 'text-foreground' :
              isActive ? 'text-primary font-medium' : 'text-muted-foreground'
            }`}
          >
            {/* Status Indicator */}
            <div className={`w-5 h-5 rounded-full flex items-center justify-center border-2 ${
                isDone ? 'bg-primary border-primary text-primary-foreground' :
                isActive ? 'border-primary' : 'border-muted'
            }`}>
                {isDone && <span className="text-[10px]">✓</span>}
                {isActive && <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />}
            </div>
            
            <span>{s.label}</span>
          </div>
        )})}
      </div>

      <div className="mt-6 text-center text-sm font-medium border-t border-border/50 pt-4">
        {status === 'complete' ? <span className="text-green-600">Processing complete</span> :
         status === 'failed'   ? <span className="text-red-500">Processing failed</span> :
         <span className="text-foreground animate-pulse">{progress}% — {stage || 'Initializing...'}</span>}
      </div>
    </div>
  )
}
