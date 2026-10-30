// 첫 답변 조각을 기다리는 동안 보여주는 점 3개. slow 이면 지연 안내를 덧붙인다
export function LoadingIndicator({ slow }: { slow?: boolean }) {
  return (
    <div>
      <span className="inline-flex gap-[5px] py-2" aria-label="답변 작성 중">
        {[0, 150, 300].map((delay) => (
          <i
            key={delay}
            className="size-[5px] animate-thinking rounded-full bg-faint"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </span>
      {slow && (
        <p className="mt-0.5 break-keep text-[13px] text-muted-foreground">
          답변이 조금 늦어지고 있어요. 무료 AI API(Gemini 무료 플랜)를 사용하고 있어 사용자가 많을 때는 응답이 느려질
          수 있어요.
        </p>
      )}
    </div>
  )
}
