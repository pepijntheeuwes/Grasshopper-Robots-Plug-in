using Grasshopper.Kernel.Types;

namespace Robots.Grasshopper;

public class GH_ServoParameters : GH_Goo<ServoParameters>
{
    public GH_ServoParameters() { Value = ServoParameters.Default; }
    public GH_ServoParameters(GH_ServoParameters goo) { Value = goo.Value; }
    public GH_ServoParameters(ServoParameters native) { Value = native; }
    public override IGH_Goo Duplicate() => new GH_ServoParameters(this);
    public override bool IsValid => true;
    public override string TypeName => "ServoParameters";
    public override string TypeDescription => "Servo motion parameters for UR robots";
    public override string ToString() => Value.ToString();

    public override bool CastFrom(object source)
    {
        switch (source)
        {
            case ServoParameters servo:
                Value = servo;
                return true;
            case GH_String text:
                {
                    string[] texts = text.Value.Split(',');
                    double[] values = new double[texts.Length];

                    for (int i = 0; i < texts.Length; i++)
                    {
                        if (!GH_Convert.ToDouble_Secondary(texts[i], ref values[i]))
                            return false;
                    }

                    if (texts.Length == 3)
                    {
                        Value = new ServoParameters(values[0], values[1], values[2]);
                        return true;
                    }

                    break;
                }
        }
        return false;
    }

    public override bool CastTo<Q>(ref Q target)
    {
        if (typeof(Q).IsAssignableFrom(typeof(ServoParameters)))
        {
            target = (Q)(object)Value;
            return true;
        }

        return false;
    }
}
