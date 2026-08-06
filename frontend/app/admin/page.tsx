// frontend/app/admin/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { DollarSign, Users, Video, AlertCircle, Shield, CheckCircle, Gift, ArrowUpRight } from 'lucide-react';

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [creditGrantAmount, setCreditGrantAmount] = useState<number>(100);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      const [metricsRes, usersRes, ticketsRes] = await Promise.all([
        fetch('/api/v1/admin/analytics'),
        fetch('/api/v1/admin/users'),
        fetch('/api/v1/admin/tickets')
      ]);

      if (metricsRes.ok) setMetrics(await metricsRes.json());
      if (usersRes.ok) setUsers(await usersRes.json());
      if (ticketsRes.ok) setTickets(await ticketsRes.json());
    } catch (e) {
      console.error("Admin fetch error", e);
    }
  };

  const handleGrantCredits = async (userId: str) => {
    await fetch(`/api/v1/admin/users/${userId}/credits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credits: creditGrantAmount, reason: "Admin Gift/Support Compensation" })
    });
    fetchAdminData();
    setSelectedUser(null);
  };

  const handlePlanChange = async (userId: str, newTier: str) => {
    await fetch(`/api/v1/admin/users/${userId}/plan`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tier: newTier })
    });
    fetchAdminData();
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 font-sans">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-8 pb-6 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-purple-600/10 border border-purple-500/30 rounded-xl text-purple-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Executive Admin Control</h1>
            <p className="text-xs text-zinc-400">Platform earnings, subscriber management & support portal</p>
          </div>
        </div>
      </div>

      {/* Analytics KPIs */}
      {metrics && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl">
            <div className="flex justify-between items-center text-zinc-400 mb-2">
              <span className="text-xs font-semibold">ESTIMATED MRR</span>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-zinc-100">${metrics.mrr_usd}</div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl">
            <div className="flex justify-between items-center text-zinc-400 mb-2">
              <span className="text-xs font-semibold">TOTAL SUBSCRIBERS</span>
              <Users className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-zinc-100">{metrics.total_users}</div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl">
            <div className="flex justify-between items-center text-zinc-400 mb-2">
              <span className="text-xs font-semibold">TOTAL RENDERS</span>
              <Video className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-zinc-100">{metrics.total_renders}</div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl">
            <div className="flex justify-between items-center text-zinc-400 mb-2">
              <span className="text-xs font-semibold">OPEN COMPLAINTS</span>
              <AlertCircle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-zinc-100">{metrics.open_tickets}</div>
          </div>
        </div>
      )}

      {/* User Administration Section */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-8">
        <h2 className="text-lg font-bold mb-4">Subscriber Database</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-zinc-300">
            <thead className="bg-zinc-950 text-zinc-500 uppercase text-[11px] font-semibold border-b border-zinc-800">
              <tr>
                <th className="p-3">User Email</th>
                <th className="p-3">Plan Tier</th>
                <th className="p-3">Credit Balance</th>
                <th className="p-3">Role</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-zinc-800/30">
                  <td className="p-3 font-medium text-zinc-100">{u.email}</td>
                  <td className="p-3">
                    <select
                      value={u.tier}
                      onChange={(e) => handlePlanChange(u.id, e.target.value)}
                      className="bg-zinc-950 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-200"
                    >
                      <option value="free">Free</option>
                      <option value="starter">Starter</option>
                      <option value="pro">Pro</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </td>
                  <td className="p-3 font-mono text-purple-400">{u.credits} cr</td>
                  <td className="p-3 capitalize">{u.role}</td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => setSelectedUser(u)}
                      className="px-3 py-1 bg-purple-600/20 text-purple-300 border border-purple-500/30 rounded-lg text-xs hover:bg-purple-600/30 transition-all flex items-center gap-1 ml-auto"
                    >
                      <Gift className="w-3 h-3" /> Grant Credits
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Gift Credits Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl w-full max-w-md">
            <h3 className="text-lg font-bold mb-2">Grant Credits to User</h3>
            <p className="text-xs text-zinc-400 mb-4">{selectedUser.email}</p>
            <input
              type="number"
              value={creditGrantAmount}
              onChange={(e) => setCreditGrantAmount(parseInt(e.target.value))}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-sm text-zinc-100 mb-4"
              placeholder="Credit Amount"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setSelectedUser(null)}
                className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-lg text-xs"
              >
                Cancel
              </button>
              <button
                onClick={() => handleGrantCredits(selectedUser.id)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-xs font-semibold"
              >
                Confirm Grant
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
