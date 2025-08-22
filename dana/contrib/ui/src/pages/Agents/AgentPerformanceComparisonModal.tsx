import React from 'react';
import { Button } from '@/components/ui/button';
import { XIcon } from 'lucide-react';
import { ChatBubbleEmpty } from 'iconoir-react';
import { IconX } from '@tabler/icons-react';

interface AgentPerformanceComparisonModalProps {
  open: boolean;
  onClose: () => void;
}

const EXAMPLE_TASKS = [
  "During ballast operations near Japan's coastline, what legal precautions must be followed to avoid violating environmental laws?",
  'A minor collision occurs in Tokyo Bay with no visible damage or injuries. What are the reporting requirements under maritime law?',
  'Design a 4-step emergency plan for a Japanese cargo vessel with lithium-ion battery cargo that catches fire near a populated harbor.',
  'Design a 4-step emergency plan for a Japanese cargo vessel with lithium-ion battery cargo that catches fire near a populated harbor.',
];

const RESPONSE_QUALITY = [
  ['Speed', '2.3s', '45s'],
  ['Accuracy', '98.7%', '73%'],
  [
    'Financial Compliance',
    <div className="flex gap-2 items-center text-gray-500">✅ SOX</div>,
    <div className="text-red-500">
      <IconX />
    </div>,
  ],
  [
    'Company Context',
    <div className="flex gap-2 items-center">✅ Full</div>,
    <div className="text-red-500">
      <IconX />
    </div>,
  ],
  [
    'Professional Format',
    <div className="flex gap-2 items-center">✅ Board</div>,
    <div className="text-red-500">
      <IconX />
    </div>,
  ],
];

const GEORGIA_RESULT = (
  <>
    Immediately notify the Japan Coast Guard about the collision, providing details such as the
    location, time, and vessels involved.
    <ul className="mt-2 ml-5 text-sm list-disc text-gray-700">
      <li>
        Exchange contact and vessel information with the other party involved in the collision. This
        includes the vessel's name, registration number, and the owner's contact information.
      </li>
      <li>
        Document the incident thoroughly by taking clear photographs of the scene, noting the time
        and location, and recording any relevant details about the circumstances and potential
        contributing factors.
      </li>
      <li>
        Submit a written report to the local maritime authority within 24 hours, detailing the
        incident and any actions taken.
      </li>
      <li>
        Retain all documentation and communication related to the incident for future reference or
        legal requirements. This includes correspondence with authorities, insurance companies, and
        other involved parties.
      </li>
    </ul>
  </>
);

const GENERIC_RESULT = (
  <>
    In the event of a minor collision in Tokyo Bay with no visible damage or injuries, Japanese
    maritime law requires that you still report the incident. It is important to implement a
    structured reporting process, such as using an Incident Management System (IMS) to ensure
    traceability and compliance. A comprehensive incident report should be logged within 24 hours,
    even if the collision appears minor. This helps in understanding the root cause and preventing
    future occurrences. Additionally, maintaining detailed records and ensuring communication with
    relevant authorities, such as the Japan Coast Guard, is crucial for compliance and safety
    management.
  </>
);

export const AgentPerformanceComparisonModal: React.FC<AgentPerformanceComparisonModalProps> = ({
  open,
  onClose,
}) => {
  if (!open) return null;
  return (
    <div className="flex fixed inset-0 z-50 justify-center items-center bg-black bg-opacity-30">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col p-8 relative overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="text-xl font-semibold">Performance Comparison</div>
          <button onClick={onClose} className="p-2 rounded hover:bg-gray-100">
            <XIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>
        <div className="flex flex-row gap-8 h-full">
          {/* Left Sidebar */}
          <div className="flex flex-col flex-shrink-0 gap-6 w-64">
            <Button variant="outline" className="flex gap-2 items-center w-full">
              <ChatBubbleEmpty className="w-4 h-4" />
              Evaluate with your task
            </Button>
            <div>
              <div className="mb-2 text-sm font-semibold text-gray-700">Example Tasks</div>
              <div className="flex flex-col gap-2">
                {EXAMPLE_TASKS.map((task, i) => (
                  <div
                    key={i}
                    className="p-3 text-xs text-gray-700 bg-gray-50 rounded-lg border border-gray-100"
                  >
                    {task}
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* Main Content */}
          <div className="flex flex-col flex-1 gap-8">
            {/* Response Quality Table */}
            <div>
              <div className="mb-2 font-semibold text-gray-700">Response Quality</div>
              <table className="overflow-hidden w-full text-sm rounded-lg border">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="p-2 text-left">No</th>
                    <th className="p-2 text-left">Response Quality</th>
                    <th className="p-2 text-left">Georgia</th>
                    <th className="p-2 text-left">Generic AI</th>
                  </tr>
                </thead>
                <tbody>
                  {RESPONSE_QUALITY.map((row, i) => (
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
            {/* Comparison Results */}
            <div>
              <div className="mb-2 font-semibold text-gray-700">Comparison Results</div>
              <div className="grid grid-cols-2 gap-6">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex gap-2 items-center mb-2">
                    <div className="flex justify-center items-center w-6 h-6 text-base font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400 rounded-full">
                      G
                    </div>
                    <span className="font-semibold text-gray-900">Georgia</span>
                  </div>
                  <div className="text-xs leading-relaxed text-gray-700">{GEORGIA_RESULT}</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="mb-2 font-semibold text-gray-900">Generic AI Model</div>
                  <div className="text-xs leading-relaxed text-gray-700">{GENERIC_RESULT}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
