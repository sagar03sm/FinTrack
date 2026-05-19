"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { ProtectedLayout } from "@/components/layout/protected-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Sparkles } from "lucide-react";

type Transaction = {
  id: string;
  type: "income" | "expense";
  amount: number;
  currency: string;
  category_id: string;
  category_name: string;
  note: string;
  date: string;
  created_at: string;
};

type Category = {
  id: string;
  name: string;
  type: string;
  color: string;
};

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<"income" | "expense">("expense");
  const [amount, setAmount] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [note, setNote] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "income" | "expense">("all");
  const [filterCategory, setFilterCategory] = useState<string>("");

  const formatIndianCurrency = (value: string) => {
    const num = parseFloat(value.replace(/,/g, ""));
    if (isNaN(num) || value === "") return value;
    return num.toLocaleString("en-IN");
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/,/g, "");
    if (value === "" || /^\d*\.?\d*$/.test(value)) {
      setAmount(formatIndianCurrency(value));
    }
  };

  const { data: transactions, isLoading, error } = useQuery<{ items: Transaction[]; total: number }>({
    queryKey: ["transactions"],
    queryFn: async () => (await api.get("/transactions")).data,
  });

  const { data: categories } = useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: async () => (await api.get("/categories")).data,
  });

  const filteredTransactions = transactions?.items?.filter((tx) => {
    const matchesSearch = searchQuery === "" || 
      tx.note?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tx.category_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === "all" || tx.type === filterType;
    const matchesCategory = filterCategory === "" || tx.category_id === filterCategory;
    return matchesSearch && matchesType && matchesCategory;
  }) || [];

  const createMutation = useMutation({
    mutationFn: async (data: { type: "income" | "expense"; amount: number; category_id: string; note: string; date: string }) =>
      (await api.post("/transactions", data)).data,
    onSuccess: async (created: Transaction) => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["analytics-summary"] });
      setOpen(false);
      setAmount("");
      setCategoryId("");
      setNote("");
      setDate(new Date().toISOString().split("T")[0]);
      toast.success("Transaction added");

      // Real-time budget threshold notification (expense only)
      if (created.type === "expense") {
        try {
          const month = new Date(created.date).toISOString().slice(0, 7);
          const progress = await (await api.get(`/analytics/budget-progress?month=${month}`)).data;
          const budget = progress?.find((b: any) => b.category_id === created.category_id);
          if (budget) {
            const pct = budget.percent ?? 0;
            if (pct >= 100) {
              toast.error(
                `Budget exceeded for ${created.category_name}! Spent ₹${budget.spent.toLocaleString("en-IN")} of ₹${budget.limit.toLocaleString("en-IN")} (${pct.toFixed(0)}%)`,
                { duration: 6000 }
              );
            } else if (pct >= 80) {
              toast.warning(
                `${created.category_name} budget at ${pct.toFixed(0)}% (₹${budget.spent.toLocaleString("en-IN")} / ₹${budget.limit.toLocaleString("en-IN")})`,
                { duration: 5000 }
              );
            }
          }
        } catch {
          // ignore — notification is best-effort
        }
      }
    },
    onError: () => {
      toast.error("Failed to add transaction");
    },
  });

  const suggestMutation = useMutation({
    mutationFn: async (data: { note: string; type: "income" | "expense" }) =>
      (await api.post("/transactions/suggest-category", data)).data,
    onSuccess: (result: { category_id: string | null; category_name: string | null; confidence: string }) => {
      if (result.category_id) {
        setCategoryId(result.category_id);
        toast.success(`Suggested: ${result.category_name} (${result.confidence} confidence)`);
      } else {
        toast.info("Could not suggest a category. Pick one manually.");
      }
    },
    onError: () => {
      toast.error("AI suggestion failed");
    },
  });

  const handleSuggest = () => {
    if (!note.trim()) {
      toast.info("Add a note first so AI can suggest a category");
      return;
    }
    suggestMutation.mutate({ note, type });
  };

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/transactions/${id}`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["analytics-summary"] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      type,
      amount: parseFloat(amount.replace(/,/g, "")),
      category_id: categoryId,
      note,
      date: new Date(date).toISOString(),
    });
  };

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Transactions</h1>
            <p className="text-muted-foreground">Manage your income and expenses</p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" /> Add Transaction
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Transaction</DialogTitle>
                <DialogDescription>Record a new income or expense</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <Label>Type</Label>
                    <select
                      value={type}
                      onChange={(e) => setType(e.target.value as "income" | "expense")}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="income">Income</option>
                      <option value="expense">Expense</option>
                    </select>
                  </div>
                  <div>
                    <Label>Amount (₹)</Label>
                    <Input
                      type="text"
                      step="0.01"
                      value={amount}
                      onChange={handleAmountChange}
                      required
                    />
                  </div>
                  <div>
                    <Label>Category</Label>
                    <select
                      value={categoryId}
                      onChange={(e) => setCategoryId(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      required
                    >
                      <option value="">Select category</option>
                      {categories
                        ?.filter((cat) => cat.type === type)
                        .map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.name}
                          </option>
                        ))}
                    </select>
                  </div>
                  <div>
                    <Label>Note</Label>
                    <div className="flex gap-2">
                      <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Uber to airport" />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleSuggest}
                        disabled={suggestMutation.isPending || !note.trim()}
                        title="AI-suggest category from note"
                      >
                        <Sparkles className="h-4 w-4 mr-1" />
                        {suggestMutation.isPending ? "..." : "Suggest"}
                      </Button>
                    </div>
                  </div>
                  <div>
                    <Label>Date</Label>
                    <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
                  </div>
                </div>
                <DialogFooter className="mt-4">
                  <Button type="submit" disabled={createMutation.isPending}>
                    {createMutation.isPending ? "Saving..." : "Save"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>All Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label>Search</Label>
                  <Input
                    placeholder="Search by note or category..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Filter by Type</Label>
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value as "all" | "income" | "expense")}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="all">All</option>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                  </select>
                </div>
                <div>
                  <Label>Filter by Category</Label>
                  <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">All Categories</option>
                    {categories?.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {error ? (
                <div className="text-red-500 text-center py-8">
                  Failed to load transactions. Please try again.
                </div>
              ) : isLoading ? (
                <p>Loading...</p>
              ) : filteredTransactions.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No transactions found matching your filters.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Note</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTransactions.map((tx) => (
                      <TableRow key={tx.id}>
                        <TableCell>{new Date(tx.date).toLocaleDateString()}</TableCell>
                        <TableCell>{tx.category_name}</TableCell>
                        <TableCell>{tx.note || "-"}</TableCell>
                        <TableCell>
                          <Badge variant={tx.type === "income" ? "default" : "destructive"}>
                            {tx.type}
                          </Badge>
                        </TableCell>
                        <TableCell className={`text-right ${tx.type === "income" ? "text-green-600" : "text-red-600"}`}>
                          ₹{tx.amount.toLocaleString("en-IN")}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteMutation.mutate(tx.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}
