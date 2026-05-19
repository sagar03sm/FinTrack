"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, ChevronLeft, ChevronRight } from "lucide-react";

type Budget = {
  id: string;
  category_id: string;
  category_name: string;
  month: string;
  limit: number;
  created_at: string;
};

type Category = {
  id: string;
  name: string;
  type: string;
  color: string;
};

export default function BudgetsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7));
  const [categoryId, setCategoryId] = useState("");
  const [limit, setLimit] = useState("");

  const formatIndianNumber = (value: string) => {
    const cleanValue = value.replace(/,/g, "");
    if (!cleanValue) return "";
    const num = parseFloat(cleanValue);
    if (isNaN(num)) return cleanValue;
    return num.toLocaleString("en-IN");
  };

  const handleLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/,/g, "");
    if (!value) {
      setLimit("");
      return;
    }
    const num = parseFloat(value);
    if (isNaN(num)) {
      setLimit(value);
      return;
    }
    setLimit(num.toLocaleString("en-IN"));
  };

  const { data: budgets, isLoading } = useQuery<Budget[]>({
    queryKey: ["budgets", currentMonth],
    queryFn: async () => (await api.get(`/budgets?month=${currentMonth}`)).data,
  });

  const { data: categories } = useQuery<Category[]>({
    queryKey: ["categories", "expense"],
    queryFn: async () => (await api.get("/categories?type=expense")).data,
  });

  const { data: budgetProgress } = useQuery<
    Array<{ category_id: string; category_name: string; limit: number; spent: number; remaining: number; percent: number }>
  >({
    queryKey: ["budget-progress", currentMonth],
    queryFn: async () => (await api.get(`/analytics/budget-progress?month=${currentMonth}`)).data,
    enabled: !!currentMonth,
  });

  const upsertMutation = useMutation({
    mutationFn: async (data: { category_id: string; month: string; limit: number }) =>
      (await api.post("/budgets", data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["budget-progress"] });
      setOpen(false);
      setCategoryId("");
      setLimit("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/budgets/${id}`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["budget-progress"] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    upsertMutation.mutate({
      category_id: categoryId,
      month: currentMonth,
      limit: parseFloat(limit.replace(/,/g, "")),
    });
  };

  const changeMonth = (delta: number) => {
    const date = new Date(currentMonth + "-01");
    date.setMonth(date.getMonth() + delta);
    setCurrentMonth(date.toISOString().slice(0, 7));
  };

  const getProgressColor = (percent: number) => {
    if (percent >= 100) return "bg-red-500";
    if (percent >= 75) return "bg-amber-500";
    return "bg-green-500";
  };

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Budgets</h1>
            <p className="text-muted-foreground">Set and track monthly spending limits</p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" /> Add Budget
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Set Budget</DialogTitle>
                <DialogDescription>Create a monthly spending limit for a category</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <Label>Category</Label>
                    <select
                      value={categoryId}
                      onChange={(e) => setCategoryId(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      required
                    >
                      <option value="">Select category</option>
                      {categories?.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>Monthly Limit (₹)</Label>
                    <Input
                      type="text"
                      step="0.01"
                      value={limit}
                      onChange={handleLimitChange}
                      required
                    />
                  </div>
                  <div>
                    <Label>Month</Label>
                    <Input value={currentMonth} readOnly />
                  </div>
                </div>
                <DialogFooter className="mt-4">
                  <Button type="submit" disabled={upsertMutation.isPending}>
                    {upsertMutation.isPending ? "Saving..." : "Save"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="flex items-center justify-between">
          <Button variant="outline" size="icon" onClick={() => changeMonth(-1)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <h2 className="text-xl font-semibold">{currentMonth}</h2>
          <Button variant="outline" size="icon" onClick={() => changeMonth(1)}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {budgetProgress?.map((bp) => (
              <Card key={bp.category_id}>
                <CardHeader>
                  <CardTitle className="text-lg">{bp.category_name || "Category"}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Spent</span>
                    <span className="font-medium">₹{bp.spent.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Limit</span>
                    <span className="font-medium">₹{bp.limit.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="font-medium">{bp.percent.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-muted">
                      <div
                        className={`h-full rounded-full ${getProgressColor(bp.percent)}`}
                        style={{ width: `${Math.min(bp.percent, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Remaining</span>
                    <span className={`font-medium ${bp.remaining >= 0 ? "text-green-600" : "text-red-600"}`}>
                      ₹{bp.remaining.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
            {budgetProgress?.length === 0 && (
              <Card className="md:col-span-2 lg:col-span-3">
                <CardContent className="p-6 text-center text-muted-foreground">
                  No budgets set for this month. Click "Add Budget" to get started.
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </ProtectedLayout>
  );
}
