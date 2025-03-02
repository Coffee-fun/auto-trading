import type React from "react";
import {useState} from "react";
import {toast} from "sonner";

import {Button} from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {Input} from "@/components/ui/input";
import {$fetch} from "@/lib/fetch";

type ApiKeys = {
  BIRDEYE_API_KEY: string;
  ANTHROPIC_KEY: string;
  SOLANA_PRIVATE_KEY: string;
  WALLET_ADDRESS: string;
};

export interface APIKeysState {
  has: string[];
  missing: string[];
}
export default function ApiKeyForm({
  onSubmit,
  apiKeys,
}: {
  onSubmit: () => void;
  apiKeys: APIKeysState;
}) {
  const [keys, setKeys] = useState<ApiKeys>({
    BIRDEYE_API_KEY: "",
    ANTHROPIC_KEY: "",
    SOLANA_PRIVATE_KEY: "",
    WALLET_ADDRESS: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const {data, error} = await $fetch("/update-keys", {
      body: Object.fromEntries(Object.entries(keys).filter(([k, v]) => !!v)),
    });

    console.log(data);
    if (error?.message) {
      return toast.error(error.message);
    }
    onSubmit();
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Enter API Keys</CardTitle>
        <CardDescription>
          Please provide your API keys to start trading
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {Object.entries(keys)
            .filter((x) => !apiKeys.has.includes(x[0]))
            .map(([key, value]) => (
              <div key={key}>
                <label htmlFor={key} className="block text-sm font-medium mb-1">
                  {key}
                </label>
                <Input
                  type="password"
                  id={key}
                  value={value}
                  onChange={(e) => setKeys({...keys, [key]: e.target.value})}
                  required
                  className="w-full"
                />
              </div>
            ))}
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full">
            Submit
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
