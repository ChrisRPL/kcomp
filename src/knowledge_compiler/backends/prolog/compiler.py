import os
from knowledge_compiler.ir.models import KnowledgeIR, Rule, Condition, Action

class PrologCompiler:
    def __init__(self, output_dir: str = "prolog/generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def compile(self, ir: KnowledgeIR) -> str:
        module_name = f"policy_{ir.document_id}"
        lines = [
            f":- module({module_name}, [",
            "    derives/3,",
            "    overrides/2",
            "]).",
            "",
            ":- discontiguous derives/3.",
            ":- discontiguous overrides/2.",
            ""
        ]

        for rule in ir.rules:
            rule_id = rule.id.lower()
            
            # Build conditions
            conditions_prolog = []
            for cond in rule.conditions:
                pred = cond.predicate
                args_str = ", ".join(pred.args)
                term = f"{pred.name}({args_str})"
                if cond.polarity == "negative":
                    term = f"neg({term})"
                conditions_prolog.append(term)
            
            # Build exceptions as negative conditions
            for exc in rule.exceptions:
                if exc.effect == "defeat_rule":
                    pred = exc.condition.predicate
                    args_str = ", ".join(pred.args)
                    term = f"neg({pred.name}({args_str}))"
                    conditions_prolog.append(term)
            
            conds_str = ",\n        ".join(conditions_prolog)
            if not conditions_prolog:
                conds_str = "true"
            
            # Build conclusion
            action = rule.conclusion
            pred = action.predicate
            args_str = ", ".join(pred.args)
            action_term = f"{pred.name}({args_str})"
            
            # Wrap in modality
            if action.modality == "obligation":
                concl_str = f"obligation({action_term})"
            elif action.modality == "permission":
                concl_str = f"permission({action_term})"
            elif action.modality == "prohibition":
                concl_str = f"prohibition({action_term})"
            else:
                concl_str = action_term # Definition, classification, etc.
            
            lines.append(f"derives(")
            lines.append(f"    {rule_id},")
            lines.append(f"    {concl_str},")
            if conditions_prolog:
                lines.append(f"    [")
                lines.append(f"        {conds_str}")
                lines.append(f"    ]")
            else:
                lines.append(f"    []")
            lines.append(f").\n")
            
            if rule.priority is not None:
                # Assuming priority is just an int, we might need a way to link overriding
                pass

        # Handle explicit overrides if they were modelled separately 
        # (For MVP, we might inject them manually or through a specific field)
        # We will add an extra method to inject raw overrides for the pilot.

        file_path = os.path.join(self.output_dir, f"{ir.document_id}.pl")
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        
        return file_path
    
    def add_override(self, document_id: str, overrider: str, overridden: str):
        file_path = os.path.join(self.output_dir, f"{document_id}.pl")
        with open(file_path, "a") as f:
            f.write(f"\noverrides({overrider.lower()}, {overridden.lower()}).\n")
