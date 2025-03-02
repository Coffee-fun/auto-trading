import {toast} from "sonner";

import {createFetch} from "@better-fetch/fetch";

type FetchError<E> = {
  message?: string;
} & {
  status: number;
  statusText: string;
};

export const $fetch = createFetch({
  baseURL: process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:8000",
  retry: {
    type: "linear",
    attempts: 3,
    delay: 1000,
  },
});

export function handleError(error?: FetchError<any> | null) {
  console.log(error);
  if (error) {
    if (error.message) toast.error(error.message);
    return true;
  }
  return false;
}
