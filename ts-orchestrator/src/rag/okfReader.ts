import * as fs from 'fs';
import * as path from 'path';

export interface OKFFormula {
  name: string;
  formula: string;
  description: string;
  target_column: string;
}

export interface OKFContext {
  title: string;
  domain: string;
  type: string;
  formulas: OKFFormula[];
  business_rules: {
    recall_priority: boolean;
    sensitive_attributes: string[];
  };
  performance_thresholds: {
    min_f1_score: number;
    min_recall: number;
  };
}

export class OKFReader {
  /**
   * Reads and parses an OKF file (.okf.md) to extract business rules and formulas
   */
  static parse(filePath: string): OKFContext {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const match = fileContent.match(/^---\r?\n([\s\S]+?)\r?\n---/);
    if (!match || !match[1]) {
      throw new Error(`Invalid OKF file format (no YAML frontmatter found): ${filePath}`);
    }

    const yamlText = match[1];
    return this.parseYaml(yamlText) as OKFContext;
  }

  /**
   * Basic and robust YAML parser handling nesting by indentation
   */
  private static parseYaml(yamlText: string): any {
    const lines = yamlText.split(/\r?\n/);
    const root: any = {};
    const stack: { indent: number; obj: any; key?: string }[] = [{ indent: -1, obj: root }];

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;

      const indent = line.length - line.trimStart().length;

      // Pop stack down to the direct parent
      while (stack.length > 1 && (stack[stack.length - 1]?.indent ?? -1) >= indent) {
        stack.pop();
      }

      const parent = stack[stack.length - 1];
      if (!parent) continue;

      if (trimmed.startsWith('-')) {
        const valueStr = trimmed.substring(1).trim();
        const parentObj = parent.key ? parent.obj[parent.key] : parent.obj;

        if (parent.key && !Array.isArray(parent.obj[parent.key])) {
          parent.obj[parent.key] = [];
        }
        
        const arrayToPush = parent.key ? parent.obj[parent.key] : null;
        if (!arrayToPush) continue;

        if (valueStr.includes(':')) {
          const [k, ...vParts] = valueStr.split(':');
          const val = this.parseValue(vParts.join(':').trim());
          const newObj = { [(k ?? '').trim()]: val };
          arrayToPush.push(newObj);
          stack.push({ indent: indent, obj: newObj });
        } else {
          arrayToPush.push(this.parseValue(valueStr));
        }
      } else if (trimmed.includes(':')) {
        const [key, ...valueParts] = trimmed.split(':');
        const k = (key ?? '').trim();
        const v = valueParts.join(':').trim();

        const targetObj = parent.key ? parent.obj[parent.key] : parent.obj;

        if (v === '') {
          targetObj[k] = {};
          stack.push({ indent: indent, obj: targetObj, key: k });
        } else {
          targetObj[k] = this.parseValue(v);
        }
      }
    }
    return root;
  }


  private static parseValue(val: string): any {
    val = val.trim();
    if (val.startsWith('"') && val.endsWith('"')) {
      return val.slice(1, -1);
    }
    if (val.startsWith("'") && val.endsWith("'")) {
      return val.slice(1, -1);
    }
    if (val === 'true') return true;
    if (val === 'false') return false;
    const num = Number(val);
    if (!isNaN(num)) return num;
    return val;
  }
}
