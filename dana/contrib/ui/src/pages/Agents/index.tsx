import { Button } from "@/components/ui/button";
import { IconPlus } from "@tabler/icons-react";
import { useNavigate } from "react-router-dom";

export default function AgentsPage() {
  const navigate = useNavigate();

  return (
    <div className="flex justify-center items-center p-8 h-full">
      <div className="flex flex-col items-center max-w-md text-center">
        {/* DXA Logo */}
        <img
          src="/static/images/empty-agent.svg"
          alt="empty dxa"
          className="width-[192px] h-[192px]"
        />

        {/* Content */}
        <h1 className="py-4 text-2xl font-semibold text-gray-900">
          No Domain-Expert Agent
        </h1>
        <p className="mb-8 leading-relaxed text-gray-600">
          Create your first Domain-Expert Agent to explore the power of agent
        </p>

        {/* New Agent Button */}
        <Button
          onClick={() => navigate("/agents/create")}
          variant="default"
          size="lg"
        >
          <IconPlus className="w-4 h-4" />
          New Agent
        </Button>
      </div>
    </div>
  );
}
