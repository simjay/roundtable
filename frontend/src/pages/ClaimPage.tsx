import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Loader2, CheckCircle, XCircle } from "lucide-react"

export function ClaimPage() {
  const { token } = useParams<{ token: string }>()
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
  const [message, setMessage] = useState("")

  useEffect(() => {
    if (!token) {
      setStatus("error")
      setMessage("No claim token provided.")
      return
    }
    // The claim endpoint returns HTML — redirect the browser to it
    // so the backend's claim page handles the logic
    window.location.href = `/claim/${token}`
  }, [token])

  // Show a brief loading state before the redirect kicks in
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="text-center">
        {status === "loading" && (
          <>
            <Loader2 className="h-8 w-8 animate-spin text-slate-400 mx-auto mb-4" />
            <p className="text-slate-400 text-sm">Processing your claim...</p>
          </>
        )}
        {status === "success" && (
          <>
            <CheckCircle className="h-8 w-8 text-green-400 mx-auto mb-4" />
            <p className="text-white font-semibold mb-2">Claimed!</p>
            <p className="text-slate-400 text-sm">{message}</p>
            <Link to="/" className="text-blue-400 hover:underline text-sm mt-4 inline-block">Go to Roundtable →</Link>
          </>
        )}
        {status === "error" && (
          <>
            <XCircle className="h-8 w-8 text-red-400 mx-auto mb-4" />
            <p className="text-white font-semibold mb-2">Invalid link</p>
            <p className="text-slate-400 text-sm">{message}</p>
            <Link to="/" className="text-blue-400 hover:underline text-sm mt-4 inline-block">Go to Roundtable →</Link>
          </>
        )}
      </div>
    </div>
  )
}
