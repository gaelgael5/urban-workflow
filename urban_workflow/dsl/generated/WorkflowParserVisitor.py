# Generated from WorkflowParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .WorkflowParser import WorkflowParser
else:
    from WorkflowParser import WorkflowParser

# This class defines a complete generic visitor for a parse tree produced by WorkflowParser.

class WorkflowParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by WorkflowParser#script.
    def visitScript(self, ctx:WorkflowParser.ScriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#script_fragment.
    def visitScript_fragment(self, ctx:WorkflowParser.Script_fragmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#script_full.
    def visitScript_full(self, ctx:WorkflowParser.Script_fullContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#concurency.
    def visitConcurency(self, ctx:WorkflowParser.ConcurencyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#define_referenciel_statement.
    def visitDefine_referenciel_statement(self, ctx:WorkflowParser.Define_referenciel_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#define_state_statement.
    def visitDefine_state_statement(self, ctx:WorkflowParser.Define_state_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#constant_declaration.
    def visitConstant_declaration(self, ctx:WorkflowParser.Constant_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#value.
    def visitValue(self, ctx:WorkflowParser.ValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#state.
    def visitState(self, ctx:WorkflowParser.StateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#initializing.
    def visitInitializing(self, ctx:WorkflowParser.InitializingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#initializing_item.
    def visitInitializing_item(self, ctx:WorkflowParser.Initializing_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#on_event_statement.
    def visitOn_event_statement(self, ctx:WorkflowParser.On_event_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#switch_state.
    def visitSwitch_state(self, ctx:WorkflowParser.Switch_stateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#execute.
    def visitExecute(self, ctx:WorkflowParser.ExecuteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#execute2.
    def visitExecute2(self, ctx:WorkflowParser.Execute2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#execute3.
    def visitExecute3(self, ctx:WorkflowParser.Execute3Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#matchings.
    def visitMatchings(self, ctx:WorkflowParser.MatchingsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#matching.
    def visitMatching(self, ctx:WorkflowParser.MatchingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#action.
    def visitAction(self, ctx:WorkflowParser.ActionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#arguments.
    def visitArguments(self, ctx:WorkflowParser.ArgumentsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#argument.
    def visitArgument(self, ctx:WorkflowParser.ArgumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#argumentValue.
    def visitArgumentValue(self, ctx:WorkflowParser.ArgumentValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#contextPath.
    def visitContextPath(self, ctx:WorkflowParser.ContextPathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#jsonPathSegment.
    def visitJsonPathSegment(self, ctx:WorkflowParser.JsonPathSegmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#rule_conditions.
    def visitRule_conditions(self, ctx:WorkflowParser.Rule_conditionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#event_declaration_statement.
    def visitEvent_declaration_statement(self, ctx:WorkflowParser.Event_declaration_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#unique_keys.
    def visitUnique_keys(self, ctx:WorkflowParser.Unique_keysContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#action_declaration_statement.
    def visitAction_declaration_statement(self, ctx:WorkflowParser.Action_declaration_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#rule_declaration_statement.
    def visitRule_declaration_statement(self, ctx:WorkflowParser.Rule_declaration_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#rule_script.
    def visitRule_script(self, ctx:WorkflowParser.Rule_scriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#compareExpression.
    def visitCompareExpression(self, ctx:WorkflowParser.CompareExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#orExpression.
    def visitOrExpression(self, ctx:WorkflowParser.OrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#andExpression.
    def visitAndExpression(self, ctx:WorkflowParser.AndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#inExpression.
    def visitInExpression(self, ctx:WorkflowParser.InExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#addExpression.
    def visitAddExpression(self, ctx:WorkflowParser.AddExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#nullExpression.
    def visitNullExpression(self, ctx:WorkflowParser.NullExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#notExpression.
    def visitNotExpression(self, ctx:WorkflowParser.NotExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#multiplyExpression.
    def visitMultiplyExpression(self, ctx:WorkflowParser.MultiplyExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#negateExpression.
    def visitNegateExpression(self, ctx:WorkflowParser.NegateExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#primary.
    def visitPrimary(self, ctx:WorkflowParser.PrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#numericLiteral.
    def visitNumericLiteral(self, ctx:WorkflowParser.NumericLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#integerLiteral.
    def visitIntegerLiteral(self, ctx:WorkflowParser.IntegerLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#stringLiteral.
    def visitStringLiteral(self, ctx:WorkflowParser.StringLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#booleanLiteral.
    def visitBooleanLiteral(self, ctx:WorkflowParser.BooleanLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#nullLiteral.
    def visitNullLiteral(self, ctx:WorkflowParser.NullLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#pathValue.
    def visitPathValue(self, ctx:WorkflowParser.PathValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#functionCall.
    def visitFunctionCall(self, ctx:WorkflowParser.FunctionCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#identifier.
    def visitIdentifier(self, ctx:WorkflowParser.IdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#parenthesized.
    def visitParenthesized(self, ctx:WorkflowParser.ParenthesizedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#parameters.
    def visitParameters(self, ctx:WorkflowParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#parameter.
    def visitParameter(self, ctx:WorkflowParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#type.
    def visitType(self, ctx:WorkflowParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#key.
    def visitKey(self, ctx:WorkflowParser.KeyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#compositekey.
    def visitCompositekey(self, ctx:WorkflowParser.CompositekeyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#comment.
    def visitComment(self, ctx:WorkflowParser.CommentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#number.
    def visitNumber(self, ctx:WorkflowParser.NumberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#numeric.
    def visitNumeric(self, ctx:WorkflowParser.NumericContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#string.
    def visitString(self, ctx:WorkflowParser.StringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by WorkflowParser#delay.
    def visitDelay(self, ctx:WorkflowParser.DelayContext):
        return self.visitChildren(ctx)



del WorkflowParser