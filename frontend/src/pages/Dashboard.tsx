import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { Building2, Upload, Calculator, FileText } from 'lucide-react';

const Dashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight text-foreground">Welcome to UMS</h1>
        <p className="text-lg text-muted-foreground mt-2">
          Urban Mining Screener - Building Materials Estimation Tool
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/estimate')}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Calculator className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Building Estimation</CardTitle>
            </div>
            <CardDescription>
              Estimate building materials based on address and archetype parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" onClick={() => navigate('/estimate')}>
              Start Estimation
            </Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/upload')}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-accent/10 rounded-lg">
                <Upload className="h-6 w-6 text-accent" />
              </div>
              <CardTitle>CSV Upload</CardTitle>
            </div>
            <CardDescription>
              Upload reference data files for products, components, and building archetypes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full" onClick={() => navigate('/upload')}>
              Manage Data
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card className="border-primary/20 bg-primary/5">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Building2 className="h-6 w-6 text-primary" />
            </div>
            <CardTitle>About UMS</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            The Urban Mining Screener is developed by <strong>revitalyze</strong> and <strong>TU Graz</strong> for the{' '}
            <strong>CircularDigiBuild</strong> project, focusing on boosting the uptake of emerging technologies in
            circular economy implementation in the construction and buildings industry.
          </p>
          <div className="flex items-start gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <p>
              This tool estimates material quantities for buildings based on reference archetypes and target building
              dimensions, supporting sustainable construction practices.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
