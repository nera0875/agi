import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { MoreVertical, Plus, Pencil, Trash2, Save, X } from "lucide-react";

interface TypeWithCount {
  name: string;
  count: number;
}

interface TypeManagementDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  types: TypeWithCount[];
  onRenameType: (oldName: string, newName: string) => Promise<void>;
  onDeleteType: (typeName: string, reassignTo?: string) => Promise<void>;
  onCreateType: (typeName: string) => Promise<void>;
}

export function TypeManagementDialog({
  open,
  onOpenChange,
  types,
  onRenameType,
  onDeleteType,
  onCreateType,
}: TypeManagementDialogProps) {
  const [editingType, setEditingType] = useState<string | null>(null);
  const [editedName, setEditedName] = useState("");
  const [newTypeName, setNewTypeName] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [typeToDelete, setTypeToDelete] = useState<TypeWithCount | null>(null);
  const [reassignTo, setReassignTo] = useState<string>("none");
  const [loading, setLoading] = useState(false);

  const handleStartEdit = (typeName: string) => {
    setEditingType(typeName);
    setEditedName(typeName);
  };

  const handleSaveEdit = async () => {
    if (!editingType || !editedName.trim() || editedName === editingType) {
      setEditingType(null);
      return;
    }

    setLoading(true);
    try {
      await onRenameType(editingType, editedName.trim());
      setEditingType(null);
      setEditedName("");
    } catch (error) {
      console.error("Failed to rename type:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingType(null);
    setEditedName("");
  };

  const handleDeleteClick = (type: TypeWithCount) => {
    setTypeToDelete(type);
    setReassignTo("none");
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!typeToDelete) return;

    setLoading(true);
    try {
      await onDeleteType(
        typeToDelete.name,
        reassignTo !== "none" ? reassignTo : undefined
      );
      setDeleteDialogOpen(false);
      setTypeToDelete(null);
      setReassignTo("none");
    } catch (error) {
      console.error("Failed to delete type:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateType = async () => {
    if (!newTypeName.trim()) return;

    setLoading(true);
    try {
      await onCreateType(newTypeName.trim());
      setNewTypeName("");
    } catch (error) {
      console.error("Failed to create type:", error);
    } finally {
      setLoading(false);
    }
  };

  const availableReassignTypes = types.filter(
    (t) => t.name !== typeToDelete?.name
  );

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage Types</DialogTitle>
            <DialogDescription>
              Add, edit, or remove memory types across your database
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Types Table */}
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type Name</TableHead>
                    <TableHead className="w-[100px]">Count</TableHead>
                    <TableHead className="w-[80px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {types.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-muted-foreground">
                        No types found
                      </TableCell>
                    </TableRow>
                  ) : (
                    types.map((type) => (
                      <TableRow key={type.name}>
                        <TableCell>
                          {editingType === type.name ? (
                            <div className="flex items-center gap-2">
                              <Input
                                value={editedName}
                                onChange={(e) => setEditedName(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleSaveEdit();
                                  if (e.key === "Escape") handleCancelEdit();
                                }}
                                autoFocus
                                disabled={loading}
                              />
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={handleSaveEdit}
                                disabled={loading}
                              >
                                <Save className="h-4 w-4" />
                              </Button>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={handleCancelEdit}
                                disabled={loading}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ) : (
                            <Badge>{type.name}</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{type.count}</Badge>
                        </TableCell>
                        <TableCell>
                          {editingType !== type.name && (
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" disabled={loading}>
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleStartEdit(type.name)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Rename
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => handleDeleteClick(type)}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Add New Type */}
            <div className="space-y-2">
              <Label>Add New Type</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Enter type name..."
                  value={newTypeName}
                  onChange={(e) => setNewTypeName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCreateType();
                  }}
                  disabled={loading}
                />
                <Button onClick={handleCreateType} disabled={loading || !newTypeName.trim()}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Type
                </Button>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Type "{typeToDelete?.name}"?</AlertDialogTitle>
            <AlertDialogDescription>
              This type is used by {typeToDelete?.count} node{typeToDelete?.count !== 1 ? 's' : ''}.
              {typeToDelete && typeToDelete.count > 0 && (
                <div className="mt-4 space-y-2">
                  <Label>Reassign nodes to:</Label>
                  <Select value={reassignTo} onValueChange={setReassignTo}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Remove type (set to null)</SelectItem>
                      {availableReassignTypes.map((t) => (
                        <SelectItem key={t.name} value={t.name}>
                          {t.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={loading}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={loading}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
