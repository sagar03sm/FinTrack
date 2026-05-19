"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProtectedLayout } from "@/components/layout/protected-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line } from "recharts";

type CategoryBreakdown = {
  category_id: string;
  category_name: string;
  type: string;
  total: number;
  count: number;
};

type MonthlyTrend = {
  month: string;
  income: number;
  expense: number;
  net: number;
};

const COLORS = ["#6366f1", "#ec4899", "#10b981", "#f59e0b", "#3b82f6", "#8b5cf6", "#ef4444", "#14b8a6"];

export default function AnalyticsPage() {
  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

  const [dateFrom, setDateFrom] = useState(startOfMonth.toISOString().split("T")[0]);
  const [dateTo, setDateTo] = useState(endOfMonth.toISOString().split("T")[0]);
  const [months, setMonths] = useState(6);

  const { data: byCategory } = useQuery<CategoryBreakdown[]>({
    queryKey: ["analytics-by-category", dateFrom, dateTo],
    queryFn: async () =>
      (
        await api.get("/analytics/by-category", {
          params: { date_from: new Date(dateFrom).toISOString(), date_to: new Date(dateTo).toISOString() },
        })
      ).data,
  });

  const { data: monthlyTrend } = useQuery<MonthlyTrend[]>({
    queryKey: ["analytics-monthly-trend", months],
    queryFn: async () => {
      const data = await (await api.get(`/analytics/monthly-trend?months=${months}`)).data;
      return data.reverse();
    },
  });

  const expenseData = byCategory?.filter((c) => c.type === "expense") || [];
  const incomeData = byCategory?.filter((c) => c.type === "income") || [];

  const pieData = expenseData.map((c, i) => ({
    name: c.category_name,
    value: c.total,
    color: COLORS[i % COLORS.length],
  }));

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Visual insights into your spending patterns</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Expense by Category</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>From</Label>
                    <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                  </div>
                  <div>
                    <Label>To</Label>
                    <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => `₹${(value ?? 0).toFixed(2)}`} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Monthly Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label>Last N Months</Label>
                  <Input
                    type="number"
                    min={1}
                    max={24}
                    value={months}
                    onChange={(e) => setMonths(Number(e.target.value))}
                  />
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={monthlyTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => `₹${value}`} />
                    <Tooltip formatter={(value: any) => `₹${(value ?? 0).toFixed(2)}`} />
                    <Legend />
                    <Bar dataKey="income" fill="#10b981" name="Income" />
                    <Bar dataKey="expense" fill="#ef4444" name="Expense" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>


        <Card>
          <CardHeader>
            <CardTitle>Category Breakdown Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="font-semibold">Expenses</div>
              {expenseData.map((c) => (
                <div key={c.category_id} className="flex justify-between items-center border-b pb-2">
                  <div>
                    <span className="font-medium">{c.category_name}</span>
                    <span className="text-sm text-muted-foreground ml-2">({c.count} transactions)</span>
                  </div>
                  <span className="font-semibold text-red-600">₹{c.total.toFixed(2)}</span>
                </div>
              ))}
              {incomeData.length > 0 && (
                <>
                  <div className="font-semibold pt-4">Income</div>
                  {incomeData.map((c) => (
                    <div key={c.category_id} className="flex justify-between items-center border-b pb-2">
                      <div>
                        <span className="font-medium">{c.category_name}</span>
                        <span className="text-sm text-muted-foreground ml-2">({c.count} transactions)</span>
                      </div>
                      <span className="font-semibold text-green-600">₹{c.total.toFixed(2)}</span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}
