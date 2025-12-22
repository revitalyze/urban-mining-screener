import {useState} from 'react';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from '@/components/ui/select';
import {Alert, AlertDescription} from '@/components/ui/alert';
import {Tabs, TabsContent, TabsList, TabsTrigger} from '@/components/ui/tabs';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/ui/table';
import {Badge} from '@/components/ui/badge';
import {
    estimateBuildingValues,
    getArchetypeOptions,
    computeArchetype,
    estimateMaterials,
    BuildingEstimationResponse,
    MaterialEstimationResponse,
    ArchetypeOptions,
    getRefurbishmentOptions,
    RefurbishmentOptionsResponse,
} from '@/services/api';
import {MapPin, Building, Ruler, Layers, AlertCircle, Loader2, Download} from 'lucide-react';
import {toast} from 'sonner';
import {useQuery} from '@tanstack/react-query';

const BuildingEstimation = () => {
    // Step 1: Address input
    const [address, setAddress] = useState('');
    const [isEstimatingBuilding, setIsEstimatingBuilding] = useState(false);
    const [buildingData, setBuildingData] = useState<BuildingEstimationResponse | null>(null);
    const [buildingError, setBuildingError] = useState<string | null>(null);

    // Step 2: Archetype selection
    const [typologie, setTypologie] = useState('');
    const [baujahr, setBaujahr] = useState('');
    const [konstruktionstyp, setKonstruktionstyp] = useState('');
    const [energieklasse, setEnergieklasse] = useState('');
    const [grundflaeche, setGrundflaeche] = useState('');
    const [gebaeudeumfang, setGebaeudeumfang] = useState('');
    const [gebaeudehoehe, setGebaeudehoehe] = useState('');
    const [isComputingArchetype, setIsComputingArchetype] = useState(false);
    const [archetypeError, setArchetypeError] = useState<string | null>(null);

    // Step 3: Refurbishment selection
    const [archetypeId, setArchetypeId] = useState<string | null>(null);
    const [refurbishmentOptions, setRefurbishmentOptions] = useState<RefurbishmentOptionsResponse | null>(null);
    const [selectedRefurbishmentLevel, setSelectedRefurbishmentLevel] = useState<string | null>(null);
    const [isLoadingRefurbishmentOptions, setIsLoadingRefurbishmentOptions] = useState(false);
    const [refurbishmentError, setRefurbishmentError] = useState<string | null>(null);

    // Step 4: Material estimation
    const [materialData, setMaterialData] = useState<MaterialEstimationResponse | null>(null);
    const [isEstimatingMaterials, setIsEstimatingMaterials] = useState(false);
    const [materialError, setMaterialError] = useState<string | null>(null);

    const [currentStep, setCurrentStep] = useState(1);

    // Fetch archetype options
    const {data: archetypeOptions} = useQuery<ArchetypeOptions>({
        queryKey: ['archetypeOptions'],
        queryFn: getArchetypeOptions,
    });

    const handleAddressSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setBuildingError(null);
        setIsEstimatingBuilding(true);

        try {
            const data = await estimateBuildingValues({address});
            setBuildingData(data);
            setGrundflaeche(data.grundflaeche.toFixed(2));
            setGebaeudeumfang(data.gebaeudeumfang.toFixed(2));
            setGebaeudehoehe(data.gebaeudehoehe?.toFixed(2) || '');
            setCurrentStep(2);
            toast.success('Building values estimated successfully');
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || 'Failed to estimate building values';
            setBuildingError(errorMsg);
            toast.error('Estimation failed');
        } finally {
            setIsEstimatingBuilding(false);
        }
    };

    const handleMaterialEstimation = async (e: React.FormEvent) => {
        e.preventDefault();
        setArchetypeError(null);
        setMaterialError(null);
        setRefurbishmentError(null);
        setIsComputingArchetype(true);

        try {
            const archetypeResponse = await computeArchetype({
                address,
                typologie,
                baujahr: parseInt(baujahr),
                konstruktionstyp: parseInt(konstruktionstyp),
                energieklasse: parseInt(energieklasse),
            });

            const newArchetypeId = String(archetypeResponse.archetype_id);
            setArchetypeId(newArchetypeId);

            setIsLoadingRefurbishmentOptions(true);
            const options = await getRefurbishmentOptions(newArchetypeId);
            setRefurbishmentOptions(options);
            setIsLoadingRefurbishmentOptions(false);

            if (!options.refurbishment_required || options.available_levels.length === 0) {
                // No refurbishment selection step needed; estimate immediately
                setIsEstimatingMaterials(true);
                const materialsResponse = await estimateMaterials({
                    archetype_id: newArchetypeId,
                    target_grundflaeche: parseFloat(grundflaeche),
                    target_gebaeudeumrisse: parseFloat(gebaeudeumfang),
                    target_gebaeudehoehe: parseFloat(gebaeudehoehe),
                });
                setMaterialData(materialsResponse);
                setCurrentStep(4);
                toast.success('Material estimation completed');
            } else {
                // Show refurbishment selection step
                setSelectedRefurbishmentLevel(options.default_level ?? 'as-built');
                setCurrentStep(3);
                toast.success('Archetype computed. Please select refurbishment level.');
            }
        } catch (err: any) {
            const errorMsg =
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Failed to compute archetype or refurbishment options';
            setArchetypeError(errorMsg);
            setRefurbishmentError(errorMsg);
            toast.error('Estimation failed');
        } finally {
            setIsComputingArchetype(false);
            setIsEstimatingMaterials(false);
            setIsLoadingRefurbishmentOptions(false);
        }
    };

    const handleRestart = () => {
        setCurrentStep(1);
        setAddress('');
        setBuildingData(null);
        setMaterialData(null);
        setTypologie('');
        setBaujahr('');
        setKonstruktionstyp('');
        setEnergieklasse('');
        setGrundflaeche('');
        setGebaeudeumfang('');
        setGebaeudehoehe('');
        setBuildingError(null);
        setArchetypeError(null);
        setMaterialError(null);
        setArchetypeId(null);
        setRefurbishmentOptions(null);
        setSelectedRefurbishmentLevel(null);
        setRefurbishmentError(null);
    };

    const handleExportCSV = () => {
        if (!materialData) return;

        // Escape a single CSV field according to RFC 4180
        const escapeCSV = (val: unknown): string => {
            if (val === null || val === undefined) return '';
            const str = String(val);
            // If field contains comma, double-quote, or newline -> wrap in quotes
            const needsQuotes = /[",\n]/.test(str);
            const escaped = str.replace(/"/g, '""');
            return needsQuotes ? `"${escaped}"` : escaped;
        };

        // Build a row safely
        const buildRow = (...fields: Array<string | number>): string =>
            fields.map(escapeCSV).join(',');

        const csvRows: string[] = [];

        // Header information
        csvRows.push('Building Material Estimation Report');
        csvRows.push(buildRow('Address', address));
        csvRows.push(buildRow('Ground Area (m²)', grundflaeche));
        csvRows.push(buildRow('Perimeter (m)', gebaeudeumfang));
        csvRows.push(buildRow('Height (m)', gebaeudehoehe));
        csvRows.push('');

        // Window data
        if (materialData.window_data && materialData.window_data.length > 0) {
            csvRows.push('Window Estimates');
            csvRows.push(buildRow('Component Type', 'Product Designation', 'Area (m²)'));
            materialData.window_data.forEach((item) => {
                csvRows.push(buildRow(item[0], item[1], item[2].toFixed(2)));
            });
            csvRows.push('');
        }

        // Materials by Element Type
        csvRows.push('Materials by Element Type');
        csvRows.push(buildRow('Element Type', 'Product', 'Volume (m³)', 'Weight (kg)'));
        materialData.by_element_type.forEach((item) => {
            csvRows.push(
                buildRow(
                    item.element_type,
                    item.product_designation,
                    item.volume.toFixed(2),
                    item.weight.toFixed(2)
                )
            );
        });
        const totalVolumeElement = materialData.by_element_type.reduce((acc, item) => acc + item.volume, 0);
        const totalWeightElement = materialData.by_element_type.reduce((acc, item) => acc + item.weight, 0);
        csvRows.push(buildRow('Total', '', totalVolumeElement.toFixed(2), totalWeightElement.toFixed(2)));
        csvRows.push('');

        // Materials by Product Category
        csvRows.push('Materials by Product Category');
        csvRows.push(buildRow('Category', 'Product', 'Total Volume (m³)', 'Total Weight (kg)'));
        materialData.by_product_category.forEach((item) => {
            csvRows.push(
                buildRow(
                    item.category,
                    item.product_designation,
                    item.total_volume.toFixed(2),
                    item.total_weight.toFixed(2)
                )
            );
        });
        const totalVolumeCategory = materialData.by_product_category.reduce(
            (acc, item) => acc + item.total_volume,
            0
        );
        const totalWeightCategory = materialData.by_product_category.reduce(
            (acc, item) => acc + item.total_weight,
            0
        );
        csvRows.push(buildRow('Total', '', totalVolumeCategory.toFixed(2), totalWeightCategory.toFixed(2)));
        csvRows.push('');

        // Category Summary
        csvRows.push('Category Summary');
        csvRows.push(buildRow('Category', 'Total Volume (m³)', 'Total Weight (kg)'));
        const categoryMap: Record<string, { volume: number; weight: number }> = {};
        materialData.by_product_category.forEach((item) => {
            const category = item.category || 'Unknown';
            if (!categoryMap[category]) {
                categoryMap[category] = { volume: 0, weight: 0 };
            }
            categoryMap[category].volume += item.total_volume;
            categoryMap[category].weight += item.total_weight;
        });
        const categories = Object.entries(categoryMap).sort((a, b) => a[0].localeCompare(b[0]));
        categories.forEach(([category, data]) => {
            csvRows.push(buildRow(category, data.volume.toFixed(2), data.weight.toFixed(2)));
        });
        const totalVolumeSummary = categories.reduce((acc, [, data]) => acc + data.volume, 0);
        const totalWeightSummary = categories.reduce((acc, [, data]) => acc + data.weight, 0);
        csvRows.push(buildRow('Total', totalVolumeSummary.toFixed(2), totalWeightSummary.toFixed(2)));

        // Create CSV content (prepend UTF-8 BOM for Excel on macOS)
        const csvContent = csvRows.join('\n');
        const BOM = '\uFEFF';
        const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', `building_estimation_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        toast.success('CSV exported successfully');
    };

    const handleRefurbishmentAndEstimate = async () => {
        if (!archetypeId) {
            setRefurbishmentError('Missing archetype identifier.');
            return;
        }
        if (!selectedRefurbishmentLevel) {
            setRefurbishmentError('Please select a refurbishment level.');
            return;
        }

        setRefurbishmentError(null);
        setMaterialError(null);
        setIsEstimatingMaterials(true);

        try {
            const materialsResponse = await estimateMaterials({
                archetype_id: archetypeId,
                target_grundflaeche: parseFloat(grundflaeche),
                target_gebaeudeumrisse: parseFloat(gebaeudeumfang),
                target_gebaeudehoehe: parseFloat(gebaeudehoehe),
                refurbishment_level: selectedRefurbishmentLevel,
            });
            setMaterialData(materialsResponse);
            setCurrentStep(4);
            toast.success('Material estimation completed');
        } catch (err: any) {
            const errorMsg =
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Failed to estimate materials with refurbishment level';
            setMaterialError(errorMsg);
            setRefurbishmentError(errorMsg);
            toast.error('Estimation failed');
        } finally {
            setIsEstimatingMaterials(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Building Material Estimation</h1>
                <p className="text-muted-foreground mt-2">Multi-step workflow for estimating building materials</p>
            </div>

            {/* Step 1: Address Input */}
            {currentStep === 1 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <MapPin className="h-5 w-5"/>
                            Step 1: Enter Building Address
                        </CardTitle>
                        <CardDescription>
                            Enter the building address to estimate its ground area, perimeter, and height
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleAddressSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="address">Building Address</Label>
                                <Input
                                    id="address"
                                    placeholder="e.g., Wastiangasse 5, Graz"
                                    value={address}
                                    onChange={(e) => setAddress(e.target.value)}
                                    disabled={isEstimatingBuilding}
                                />
                            </div>

                            {buildingError && (
                                <Alert variant="destructive">
                                    <AlertCircle className="h-4 w-4"/>
                                    <AlertDescription>{buildingError}</AlertDescription>
                                </Alert>
                            )}

                            <Button type="submit" disabled={isEstimatingBuilding || !address} className="w-full">
                                {isEstimatingBuilding ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin"/>
                                        Estimating...
                                    </>
                                ) : (
                                    'Estimate Building Values'
                                )}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Step 2: Archetype Selection & Material Estimation */}
            {currentStep === 2 && buildingData && (
                <div className="space-y-6">
                    <Card className="border-success bg-success/5">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-success">
                                <Building className="h-5 w-5"/>
                                Building Values Estimated
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4 md:grid-cols-4">
                                <div>
                                    <p className="text-sm text-muted-foreground">Ground Area</p>
                                    <p className="text-2xl font-bold">{buildingData.grundflaeche.toFixed(2)} m²</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Perimeter</p>
                                    <p className="text-2xl font-bold">{buildingData.gebaeudeumfang.toFixed(2)} m</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Height</p>
                                    <p className="text-2xl font-bold">
                                        {buildingData.gebaeudehoehe ? `${buildingData.gebaeudehoehe.toFixed(2)} m` : 'N/A'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Country</p>
                                    <Badge variant="outline" className="text-lg mt-1">
                                        {buildingData.country_code}
                                    </Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Layers className="h-5 w-5"/>
                                Step 2: Select Archetype Parameters
                            </CardTitle>
                            <CardDescription>Provide building characteristics to determine the material
                                archetype</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleMaterialEstimation} className="space-y-6">
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label htmlFor="typologie">Typologie</Label>
                                        <Select value={typologie} onValueChange={setTypologie}>
                                            <SelectTrigger id="typologie">
                                                <SelectValue placeholder="Select typologie"/>
                                            </SelectTrigger>
                                            <SelectContent>
                                                {archetypeOptions?.typologie.map((opt) => (
                                                    <SelectItem key={opt.code} value={opt.code}>
                                                        {opt.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="baujahr">Construction Year (Baujahr)</Label>
                                        <Input
                                            id="baujahr"
                                            type="number"
                                            min={1800}
                                            max={2100}
                                            placeholder="e.g., 1990"
                                            value={baujahr}
                                            onChange={(e) => setBaujahr(e.target.value)}
                                        />
                                    </div>


                                    <div className="space-y-2">
                                        <Label htmlFor="konstruktionstyp">Construction Type (Konstruktionstyp)</Label>
                                        <Select value={konstruktionstyp} onValueChange={setKonstruktionstyp}>
                                            <SelectTrigger id="konstruktionstyp">
                                                <SelectValue placeholder="Select construction type"/>
                                            </SelectTrigger>
                                            <SelectContent>
                                                {/* 1. Add 'index' to the map arguments to help create a unique key */}
                                                {archetypeOptions?.konstruktionstyp.map((opt, index) => (
                                                    <SelectItem
                                                        /* 2. Make the React key unique using the index */
                                                        key={`${opt.code}-${index}`}

                                                        /* 3. Make the value unique by combining code and label */
                                                        value={`${opt.code}-${opt.label}`}
                                                    >
                                                        {opt.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>


                                    <div className="space-y-2">
                                        <Label htmlFor="energieklasse">Energy Class (Energieklasse)</Label>
                                        <Select value={energieklasse} onValueChange={setEnergieklasse}>
                                            <SelectTrigger id="energieklasse">
                                                <SelectValue placeholder="Select energy class"/>
                                            </SelectTrigger>
                                            <SelectContent>
                                                {archetypeOptions?.energieklasse.map((opt) => (
                                                    <SelectItem key={opt.code} value={opt.code.toString()}>
                                                        {opt.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <h3 className="text-sm font-medium">Building Dimensions (editable)</h3>
                                    <div className="grid gap-4 md:grid-cols-3">
                                        <div className="space-y-2">
                                            <Label htmlFor="grundflaeche">Ground Area (m²)</Label>
                                            <Input
                                                id="grundflaeche"
                                                type="number"
                                                step="0.01"
                                                value={grundflaeche}
                                                onChange={(e) => setGrundflaeche(e.target.value)}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="gebaeudeumfang">Perimeter (m)</Label>
                                            <Input
                                                id="gebaeudeumfang"
                                                type="number"
                                                step="0.01"
                                                value={gebaeudeumfang}
                                                onChange={(e) => setGebaeudeumfang(e.target.value)}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="gebaeudehoehe">Height (m)</Label>
                                            <Input
                                                id="gebaeudehoehe"
                                                type="number"
                                                step="0.01"
                                                value={gebaeudehoehe}
                                                onChange={(e) => setGebaeudehoehe(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {
                                    archetypeError && (
                                        <Alert variant="destructive">
                                            <AlertCircle className="h-4 w-4"/>
                                            <AlertDescription>{archetypeError}</AlertDescription>
                                        </Alert>
                                    )
                                }

                                <div className="flex gap-3">
                                    <Button type="button" variant="outline" onClick={handleRestart}>
                                        Start Over
                                    </Button>
                                    <Button
                                        type="submit"
                                        disabled={
                                            isComputingArchetype ||
                                            isEstimatingMaterials ||
                                            !typologie ||
                                            !baujahr ||
                                            !konstruktionstyp ||
                                            !energieklasse ||
                                            !grundflaeche ||
                                            !gebaeudeumfang ||
                                            !gebaeudehoehe
                                        }
                                        className="flex-1"
                                    >
                                        {isComputingArchetype || isEstimatingMaterials ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin"/>
                                                Estimating...
                                            </>
                                        ) : (
                                            'Continue'
                                        )}
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Step 3: Refurbishment Selection */}
            {currentStep === 3 && refurbishmentOptions && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Layers className="h-5 w-5" />
                            Step 3: Select Refurbishment Level
                        </CardTitle>
                        <CardDescription>
                            {refurbishmentOptions.explanation ??
                                'Select a refurbishment level. "As-built (no refurbishment)" keeps the building in its current state.'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {isLoadingRefurbishmentOptions ? (
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading refurbishment options...
                            </div>
                        ) : (
                            <>
                                {refurbishmentError && (
                                    <Alert variant="destructive">
                                        <AlertCircle className="h-4 w-4" />
                                        <AlertDescription>{refurbishmentError}</AlertDescription>
                                    </Alert>
                                )}

                                <div className="space-y-2">
                                    <Label htmlFor="refurbishment-level">Refurbishment Level</Label>
                                    <Select
                                        value={selectedRefurbishmentLevel ?? ''}
                                        onValueChange={setSelectedRefurbishmentLevel}
                                    >
                                        <SelectTrigger id="refurbishment-level">
                                            <SelectValue placeholder="Select refurbishment level" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {/* Always allow as-built */}
                                            <SelectItem value="as-built">
                                                As-built (no refurbishment)
                                            </SelectItem>

                                            {/* Then all other levels from backend */}
                                            {refurbishmentOptions.available_levels
                                                .filter((level) => level !== 'as-built')
                                                .map((level) => {
                                                    const label = level.charAt(0).toUpperCase() + level.slice(1);
                                                    return (
                                                        <SelectItem key={level} value={level}>
                                                            {label}
                                                        </SelectItem>
                                                    );
                                                })}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="flex gap-3">
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => {
                                            setCurrentStep(2);
                                        }}
                                    >
                                        Back
                                    </Button>
                                    <Button
                                        type="button"
                                        className="flex-1"
                                        disabled={isEstimatingMaterials || !selectedRefurbishmentLevel}
                                        onClick={handleRefurbishmentAndEstimate}
                                    >
                                        {isEstimatingMaterials ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Estimating Materials...
                                            </>
                                        ) : (
                                            'Estimate Materials'
                                        )}
                                    </Button>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Step 4: Results */}
            {currentStep === 4 && materialData && (
                <div className="space-y-6">
                    <Card className="border-success bg-success/5">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-success">
                                <Building className="h-5 w-5"/>
                                Estimation Complete
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4 md:grid-cols-4">
                                <div>
                                    <p className="text-sm text-muted-foreground">Ground Area</p>
                                    <p className="text-2xl font-bold">{grundflaeche} m²</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Perimeter</p>
                                    <p className="text-2xl font-bold">{gebaeudeumfang} m</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Height</p>
                                    <p className="text-2xl font-bold">{gebaeudehoehe} m</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Address</p>
                                    <p className="text-sm font-medium truncate">{address}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {materialData.window_data && materialData.window_data.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Window Estimates</CardTitle>
                                <CardDescription>Estimated window areas for the building</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="rounded-md border">
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead>Component Type</TableHead>
                                                <TableHead>Product Designation</TableHead>
                                                <TableHead className="text-right">Area (m²)</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {materialData.window_data.map((item, idx) => (
                                                <TableRow key={idx}>
                                                    <TableCell className="font-medium">{item[0]}</TableCell>
                                                    <TableCell>{item[1]}</TableCell>
                                                    <TableCell className="text-right">{item[2].toFixed(2)}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    <Card>
                        <CardHeader>
                            <CardTitle>Material Estimation Results</CardTitle>
                            <CardDescription>Detailed breakdown of estimated building materials</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Tabs defaultValue="element">
                                <TabsList className="grid w-full grid-cols-3">
                                    <TabsTrigger value="element">By Element Type</TabsTrigger>
                                    <TabsTrigger value="category">By Product Category</TabsTrigger>
                                    <TabsTrigger value="summary">Category Summary</TabsTrigger>
                                </TabsList>
                                <TabsContent value="element" className="space-y-4">
                                    <div className="rounded-md border">
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>Element Type</TableHead>
                                                    <TableHead>Product</TableHead>
                                                    <TableHead className="text-right">Volume (m³)</TableHead>
                                                    <TableHead className="text-right">Weight (kg)</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {materialData.by_element_type.map((item, idx) => (
                                                    <TableRow key={idx}>
                                                        <TableCell
                                                            className="font-medium">{item.element_type}</TableCell>
                                                        <TableCell>{item.product_designation}</TableCell>
                                                        <TableCell
                                                            className="text-right">{item.volume.toFixed(2)}</TableCell>
                                                        <TableCell
                                                            className="text-right">{item.weight.toFixed(2)}</TableCell>
                                                    </TableRow>
                                                ))}
                                                <TableRow className="font-bold bg-muted/50">
                                                    <TableCell colSpan={2}>Total</TableCell>
                                                    <TableCell className="text-right">
                                                        {materialData.by_element_type
                                                            .reduce((acc, item) => acc + item.volume, 0)
                                                            .toFixed(2)}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        {materialData.by_element_type
                                                            .reduce((acc, item) => acc + item.weight, 0)
                                                            .toFixed(2)}
                                                    </TableCell>
                                                </TableRow>
                                            </TableBody>
                                        </Table>
                                    </div>
                                </TabsContent>
                                <TabsContent value="category" className="space-y-4">
                                    <div className="rounded-md border">
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>Category</TableHead>
                                                    <TableHead>Product</TableHead>
                                                    <TableHead className="text-right">Total Volume (m³)</TableHead>
                                                    <TableHead className="text-right">Total Weight (kg)</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {materialData.by_product_category.map((item, idx) => (
                                                    <TableRow key={idx}>
                                                        <TableCell className="font-medium">{item.category}</TableCell>
                                                        <TableCell>{item.product_designation}</TableCell>
                                                        <TableCell
                                                            className="text-right">{item.total_volume.toFixed(2)}</TableCell>
                                                        <TableCell
                                                            className="text-right">{item.total_weight.toFixed(2)}</TableCell>
                                                    </TableRow>
                                                ))}
                                                <TableRow className="font-bold bg-muted/50">
                                                    <TableCell colSpan={2}>Total</TableCell>
                                                    <TableCell className="text-right">
                                                        {materialData.by_product_category
                                                            .reduce((acc, item) => acc + item.total_volume, 0)
                                                            .toFixed(2)}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        {materialData.by_product_category
                                                            .reduce((acc, item) => acc + item.total_weight, 0)
                                                            .toFixed(2)}
                                                    </TableCell>
                                                </TableRow>
                                            </TableBody>
                                        </Table>
                                    </div>
                                </TabsContent>
                                <TabsContent value="summary" className="space-y-4">
                                    <div className="rounded-md border">
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>Category</TableHead>
                                                    <TableHead className="text-right">Total Volume (m³)</TableHead>
                                                    <TableHead className="text-right">Total Weight (kg)</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {(() => {
                                                    const categoryMap: Record<string, {
                                                        volume: number;
                                                        weight: number
                                                    }> = {};
                                                    materialData.by_product_category.forEach((item) => {
                                                        const category = item.category || 'Unknown';
                                                        if (!categoryMap[category]) {
                                                            categoryMap[category] = {volume: 0, weight: 0};
                                                        }
                                                        categoryMap[category].volume += item.total_volume;
                                                        categoryMap[category].weight += item.total_weight;
                                                    });
                                                    const categories = Object.entries(categoryMap).sort((a, b) =>
                                                        a[0].localeCompare(b[0])
                                                    );
                                                    const totalVolume = categories.reduce((acc, [, data]) => acc + data.volume, 0);
                                                    const totalWeight = categories.reduce((acc, [, data]) => acc + data.weight, 0);

                                                    return (
                                                        <>
                                                            {categories.map(([category, data]) => (
                                                                <TableRow key={category}>
                                                                    <TableCell
                                                                        className="font-medium">{category}</TableCell>
                                                                    <TableCell
                                                                        className="text-right">{data.volume.toFixed(2)}</TableCell>
                                                                    <TableCell
                                                                        className="text-right">{data.weight.toFixed(2)}</TableCell>
                                                                </TableRow>
                                                            ))}
                                                            <TableRow className="font-bold bg-muted/50">
                                                                <TableCell>Total</TableCell>
                                                                <TableCell
                                                                    className="text-right">{totalVolume.toFixed(2)}</TableCell>
                                                                <TableCell
                                                                    className="text-right">{totalWeight.toFixed(2)}</TableCell>
                                                            </TableRow>
                                                        </>
                                                    );
                                                })()}
                                            </TableBody>
                                        </Table>
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>

                    <div className="flex justify-end gap-3">
                        <Button variant="outline" onClick={handleExportCSV}>
                            <Download className="mr-2 h-4 w-4"/>
                            Export CSV
                        </Button>
                        <Button onClick={handleRestart}>Start New Estimation</Button>
                    </div>
                </div>
            )}

            <p className="text-xs text-muted-foreground border-t pt-4">
                Data © OpenStreetMap contributors, licensed under ODbL 1.0. See the{' '}
                <a
                    href="https://www.openstreetmap.org/copyright"
                    target="_blank"
                    rel="noreferrer"
                    className="underline underline-offset-2"
                >
                    OpenStreetMap Copyright
                </a>
                {' '}and{' '}
                <a
                    href="https://opendatacommons.org/licenses/odbl/1-0/"
                    target="_blank"
                    rel="noreferrer"
                    className="underline underline-offset-2"
                >
                    ODbL 1.0
                </a>
                .
            </p>
        </div>
    );
};

export default BuildingEstimation;
