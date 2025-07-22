import React from 'react';
import { Button } from '@/components/ui/button';

const OverviewTab: React.FC<{ tpl: any; onShowComparison: () => void }> = ({ tpl, onShowComparison }) => (
  <div className="flex flex-col md:flex-row gap-8">
    <div className="flex-1 bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${tpl.avatarColor} flex items-center justify-center text-white text-xl font-bold`}></div>
        <div>
          <div className="text-lg font-semibold text-gray-900">Agent name</div>
          <div className="text-2xl font-bold text-gray-900">{tpl.name}</div>
        </div>
      </div>
      <div className="mb-4">
        <div className="text-sm text-gray-500 font-semibold mb-1">Agent Profile</div>
        <div className="text-sm text-gray-700 mb-1"><b>Role:</b> {tpl.profile?.role || tpl.title}</div>
        <div className="text-sm text-gray-700 mb-1"><b>Personality:</b> {tpl.profile?.personality || '-'}</div>
        <div className="text-sm text-gray-700 mb-1"><b>Communication style:</b> {tpl.profile?.communication || '-'}</div>
        <div className="text-sm text-gray-700 mb-1"><b>Specialties:</b> {tpl.profile?.specialties || '-'}</div>
      </div>
      <div className="mb-4">
        <div className="text-sm text-gray-500 font-semibold mb-1">Agent Performance</div>
        <table className="w-full text-sm border rounded-lg overflow-hidden">
          <thead>
            <tr className="bg-gray-50">
              <th className="p-2 text-left">No</th>
              <th className="p-2 text-left">Response Quality</th>
              <th className="p-2 text-left">{tpl.name}</th>
              <th className="p-2 text-left">Generic AI</th>
            </tr>
          </thead>
          <tbody>
            {tpl.performance?.map((row: any, i: number) => (
              <tr key={i} className="border-t">
                <td className="p-2">{i + 1}</td>
                <td className="p-2">{row[0]}</td>
                <td className="p-2">{row[1]}</td>
                <td className="p-2">{row[2]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Button variant="outline" className="mt-2" onClick={onShowComparison}>Performance Comparison</Button>
    </div>
  </div>
);

export default OverviewTab; 