namespace Robots.Grasshopper;

public class ServoParametersParameter : GH_PersistentParam<GH_ServoParameters>
{
    public ServoParametersParameter() : base("Servo parameters", "Servo", "Servo motion parameters for UR robots", "Robots", "Parameters") { }
    public override GH_Exposure Exposure => GH_Exposure.tertiary;
    protected override System.Drawing.Bitmap Icon => Util.GetIcon("iconSpeed");
    public override Guid ComponentGuid => new("{E8A5F7C2-3B4D-4E6F-9A1C-2D3E4F5A6B7C}");
    protected override GH_ServoParameters PreferredCast(object data) =>
        data is ServoParameters cast ? new GH_ServoParameters(cast) : null!;

    protected override GH_GetterResult Prompt_Singular(ref GH_ServoParameters value)
    {
        value = new GH_ServoParameters();
        return GH_GetterResult.success;
    }

    protected override GH_GetterResult Prompt_Plural(ref List<GH_ServoParameters> values)
    {
        values = [];
        return GH_GetterResult.success;
    }
}
