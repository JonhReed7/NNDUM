import { useEffect, useRef, useState } from 'react';

export function useAuthSubmit(callbackError) {
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(null);
  const request = useRef(null);

  useEffect(() => () => request.current?.abort(), []);

  async function submit(action, run) {
    if (request.current) return;

    const controller = new AbortController();
    request.current = controller;
    setError('');
    setPending(action);
    try {
      await run(controller.signal);
    } catch (error) {
      if (!controller.signal.aborted) setError(error.message);
    } finally {
      request.current = null;
      if (!controller.signal.aborted) setPending(null);
    }
  }

  return { error: error ?? callbackError, pending, submit };
}
