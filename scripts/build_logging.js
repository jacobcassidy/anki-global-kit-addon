import { stdout } from 'node:process';

export function formatBuildMessage(message) {
  const now = new Date();
  const timestamp = [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map((part) => String(part).padStart(2, '0'))
    .join(':');
  const spacing = Math.max(2, (stdout.columns ?? 0) - message.length - timestamp.length);
  return `${message}${' '.repeat(spacing)}${timestamp}`;
}
