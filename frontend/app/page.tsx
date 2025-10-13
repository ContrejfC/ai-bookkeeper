import AppShell from "@/components/layout/AppShell";
import { Card, CardHeader, CardBody } from "@nextui-org/react";

const Metric = ({ label, value }: {label: string; value: string}) => (
  <Card className="rounded-2xl">
    <CardHeader className="text-sm opacity-60">{label}</CardHeader>
    <CardBody className="text-2xl font-semibold">{value}</CardBody>
  </Card>
);

export default function Page() {
  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-sm opacity-60 mt-1">Calibrated, explainable bookkeeping automation</p>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Unposted txns" value="47" />
          <Metric label="Recon match rate" value="92%" />
          <Metric label="Vendors w/ rules" value="21" />
          <Metric label="Last export" value="Today 9:42a" />
        </div>

        <Card className="rounded-2xl">
          <CardHeader>
            <h3 className="text-lg font-semibold">Recent Activity</h3>
          </CardHeader>
          <CardBody>
            <div className="text-sm opacity-60">
              <p>• 12 transactions reviewed today</p>
              <p>• 3 new vendor rules created</p>
              <p>• Weekly access snapshot completed</p>
              <p>• Backup verification: PASS</p>
            </div>
          </CardBody>
        </Card>
      </div>
    </AppShell>
  );
}

