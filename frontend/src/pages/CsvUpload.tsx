import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { uploadCSVs, CSVUploadResponse } from '@/services/api';
import { Upload, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const CsvUpload = () => {
  const [productList, setProductList] = useState<File | null>(null);
  const [componentsList, setComponentsList] = useState<File | null>(null);
  const [buildingList, setBuildingList] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<CSVUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!productList || !componentsList || !buildingList) {
      setError('Please select all three CSV files.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await uploadCSVs(productList, componentsList, buildingList);
      setResult(response);
      toast.success('CSV files uploaded successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'An error occurred while uploading the CSV files.';
      setError(errorMsg);
      toast.error('Upload failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">CSV Data Upload</h1>
        <p className="text-muted-foreground mt-2">
          Upload reference datasets to populate the system database
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Reference Data</CardTitle>
          <CardDescription>
            Upload the three CSV files containing product, component, and building archetype data. This will replace
            all existing data in the database.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="product-list" className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Product List CSV
                </Label>
                <Input
                  id="product-list"
                  type="file"
                  accept=".csv"
                  onChange={(e) => setProductList(e.target.files?.[0] || null)}
                  disabled={isLoading}
                />
                <p className="text-sm text-muted-foreground">
                  Contains product details (ID, Category, Raw density)
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="components-list" className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Components List CSV
                </Label>
                <Input
                  id="components-list"
                  type="file"
                  accept=".csv"
                  onChange={(e) => setComponentsList(e.target.files?.[0] || null)}
                  disabled={isLoading}
                />
                <p className="text-sm text-muted-foreground">
                  Lists components with products, layer thickness, and percentage
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="building-list" className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Building List CSV
                </Label>
                <Input
                  id="building-list"
                  type="file"
                  accept=".csv"
                  onChange={(e) => setBuildingList(e.target.files?.[0] || null)}
                  disabled={isLoading}
                />
                <p className="text-sm text-muted-foreground">
                  Contains archetype data (archetype ID, reference areas, component IDs)
                </p>
              </div>
            </div>

            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Upload className="mr-2 h-4 w-4 animate-pulse" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload CSV Files
                </>
              )}
            </Button>
          </form>

          {result && (
            <Alert className="mt-6 border-success bg-success/5">
              <CheckCircle2 className="h-4 w-4 text-success" />
              <AlertTitle className="text-success">Upload Successful</AlertTitle>
              <AlertDescription>
                <div className="mt-2 space-y-1 text-sm">
                  <p>{result.message}</p>
                  <ul className="list-disc list-inside space-y-0.5 mt-2 text-muted-foreground">
                    <li>Archetypes: {result.processed_archetypes}</li>
                    <li>Element Types: {result.processed_element_types}</li>
                    <li>Components: {result.processed_components}</li>
                    <li>Products: {result.processed_products}</li>
                    <li>Component Products: {result.processed_component_products}</li>
                    <li>Archetype Elements: {result.processed_archetype_elements}</li>
                    <li>Element Components: {result.processed_element_components}</li>
                  </ul>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive" className="mt-6">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Upload Failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CsvUpload;
