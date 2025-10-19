import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { useState, useEffect } from "react";

interface EditNodeDialogProps {
  node: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (nodeId: string, properties: Record<string, any>) => Promise<void>;
}

export function EditNodeDialog({ node, open, onOpenChange, onSave }: EditNodeDialogProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);

  // Initialize form data when node changes
  useEffect(() => {
    if (node) {
      setFormData({
        text: node.text || node.content || "",
        type: node.type || "",
        status: node.status || "active",
        ...node
      });
    }
  }, [node]);

  const handleSave = async () => {
    if (!node?._id) return;

    setSaving(true);
    try {
      // Extract only editable fields
      const editableProps = {
        text: formData.text,
        type: formData.type,
        status: formData.status
      };

      await onSave(node._id, editableProps);
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to save node:", error);
    } finally {
      setSaving(false);
    }
  };

  if (!node) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Edit Memory Node</DialogTitle>
          <DialogDescription>
            Update the properties of this memory node
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="id">ID (Read-only)</Label>
            <Input
              id="id"
              value={node._id || ""}
              disabled
              className="font-mono text-xs"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="text">Text / Content</Label>
            <Textarea
              id="text"
              value={formData.text || ""}
              onChange={(e) => setFormData({ ...formData, text: e.target.value })}
              rows={4}
              placeholder="Enter memory text..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="type">Type</Label>
              <Input
                id="type"
                value={formData.type || ""}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                placeholder="e.g., context, preference"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Input
                id="status"
                value={formData.status || ""}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                placeholder="active, archived"
              />
            </div>
          </div>

          {node.timestamp && (
            <div className="space-y-2">
              <Label>Timestamp (Read-only)</Label>
              <Input
                value={new Date(node.timestamp).toLocaleString()}
                disabled
              />
            </div>
          )}

          {node._labels && node._labels.length > 0 && (
            <div className="space-y-2">
              <Label>Labels</Label>
              <div className="flex gap-2">
                {node._labels.map((label: string) => (
                  <Badge key={label} variant="secondary">{label}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
