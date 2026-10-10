import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, AlertCircle } from 'lucide-react';
import { DocumentStatusType } from '../../types/document';
import { Badge } from '../common/Badge';

interface DocumentStatusProps {
  status: DocumentStatusType;
}

export const DocumentStatus: React.FC<DocumentStatusProps> = ({ status }) => {
  switch (status) {
    case 'Uploaded':
      return (
        <Badge variant="success" icon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}>
          Uploaded
        </Badge>
      );
    case 'Under Validation':
      return (
        <Badge variant="info" icon={<Clock className="w-3.5 h-3.5 text-sky-600 animate-spin" />}>
          Under Validation
        </Badge>
      );
    case 'Pending':
      return (
        <Badge variant="warning" icon={<Clock className="w-3.5 h-3.5 text-amber-600" />}>
          Pending
        </Badge>
      );
    case 'Missing':
      return (
        <Badge variant="danger" icon={<AlertTriangle className="w-3.5 h-3.5 text-rose-600" />}>
          Missing
        </Badge>
      );
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
};
